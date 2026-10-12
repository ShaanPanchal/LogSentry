// A message box in the A2 "alert" style. The label ("Error:", "Success:" or "Note:") means the kind is clear without
// relying on colour. Errors are announced at once (role "alert"); the others politely (role "status").
const LABELS = { error: 'Error:', success: 'Success:', info: 'Note:' };

export default function Notice({ kind, children }) {
  const isError = kind === 'error';
  return (
    <div className={`alert${isError ? '' : ' info'}`} role={isError ? 'alert' : 'status'}>
      <strong>{LABELS[kind]}</strong> {children}
    </div>
  );
}
