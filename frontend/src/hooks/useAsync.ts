import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../services/api';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

/**
 * Runs an async loader and tracks its state. Results from a superseded call are
 * discarded so a slow response cannot overwrite a newer one.
 */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null });
  const callId = useRef(0);

  const run = useCallback(() => {
    const id = ++callId.current;
    setState((previous) => ({ ...previous, loading: true, error: null }));
    loader()
      .then((data) => {
        if (id === callId.current) setState({ data, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (id !== callId.current) return;
        setState({
          data: null,
          loading: false,
          error:
            error instanceof ApiError
              ? error
              : new ApiError(0, 'UNKNOWN', 'Something went wrong. Please try again.'),
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    run();
  }, [run]);

  return { ...state, reload: run, setData: (data: T) => setState({ data, loading: false, error: null }) };
}
