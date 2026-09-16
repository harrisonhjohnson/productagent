import { InstallLine } from './install-line';

export function Closing() {
  return (
    <section className="closing" aria-labelledby="closing-heading">
      <p className="section-label">TONIGHT</p>
      <h2 id="closing-heading">Close the lid tonight.</h2>
      <p className="closing-lede">
        One line installs the machine and asks four questions. The empty loops file stops being empty. In the
        morning there are four sentences waiting for you.
      </p>
      <InstallLine />
    </section>
  );
}
