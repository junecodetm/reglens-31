export function PageNav() {
  return (
    <nav className="page-nav" aria-label="Section navigation">
      <div className="content-bound page-nav-scroll">
        <ul className="page-nav-list">
          <li>
            <a className="page-nav-link" href="#about">About</a>
          </li>
          <li>
            <a className="page-nav-link" href="#extraction">Extraction</a>
          </li>
          <li>
            <a className="page-nav-link" href="#explore">Explore</a>
          </li>
          <li>
            <a className="page-nav-link" href="#ogc01">OGC-01 modules</a>
          </li>
          <li>
            <a className="page-nav-link" href="#evaluation">Evaluation</a>
          </li>
        </ul>
      </div>
    </nav>
  );
}
