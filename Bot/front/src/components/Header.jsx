/** Encabezado de cada sección. */
export default function Header({ title, subtitle }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <span className="page-header__hint">
        Los datos se muestran solo con autorización vigente
      </span>
    </header>
  );
}
