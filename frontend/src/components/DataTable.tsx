interface Props {
  columns: string[];
  rows: Record<string, string>[];
  caption?: string;
}

export function DataTable({ columns, rows, caption }: Props) {
  return (
    <div className="table-wrapper">
      <table>
        {caption ? <caption className="muted" style={{ padding: 8 }}>{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => {
                const value = row[column] ?? '';
                const missing = value === '(missing)';
                return (
                  <td key={column} className={missing ? 'cell-missing' : undefined}>
                    {missing ? '—' : value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
