// A message box in the A2 "alert" style. The label ("Error:" / "Note:") means the kind is clear without relying on colour.
export default function Notice({ kind, children }) {
  const isError = kind === 'error';
  return (
    <div className={`alert${isError ? '' : ' info'}`} role={isError ? 'alert' : 'status'}>
      <strong>{isError ? 'Error:' : 'Note:'}</strong> {children}
    </div>
  );
}
