const REPO = "Reaccionador2Jeje/Gold-Diamond-Browser";

document.getElementById("year").textContent = new Date().getFullYear();

const menuToggle = document.getElementById("menu-toggle");
const mainNav = document.getElementById("main-nav");
menuToggle.addEventListener("click", () => {
  const open = mainNav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(open));
});
mainNav.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
  mainNav.classList.remove("open");
  menuToggle.setAttribute("aria-expanded", "false");
}));

function formatDate(value) {
  if (!value) return "Fecha no disponible";
  return new Intl.DateTimeFormat("es-CL", { dateStyle: "long" }).format(new Date(value));
}

async function loadLatestRelease() {
  const version = document.getElementById("release-version");
  const date = document.getElementById("release-date");
  const assets = document.getElementById("release-assets");
  const status = document.getElementById("release-status");

  try {
    const response = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { Accept: "application/vnd.github+json" }
    });
    if (response.status === 404) {
      version.textContent = "Aún no hay versión estable";
      date.textContent = "Todavía no se ha publicado una release marcada como estable.";
      status.textContent = "Puedes consultar el repositorio para seguir el desarrollo.";
      return;
    }
    if (!response.ok) throw new Error(`GitHub respondió ${response.status}`);

    const release = await response.json();
    version.textContent = release.name || release.tag_name || "Versión disponible";
    date.textContent = `Publicada el ${formatDate(release.published_at)}`;
    assets.replaceChildren();

    const files = Array.isArray(release.assets) ? release.assets : [];
    if (!files.length) {
      status.textContent = "Esta publicación no contiene instaladores adjuntos. Revisa sus notas en GitHub.";
    } else {
      files.forEach(file => {
        const link = document.createElement("a");
        link.className = "asset-link";
        link.href = file.browser_download_url;
        link.target = "_blank";
        link.rel = "noopener";
        const name = document.createElement("span");
        name.textContent = file.name;
        const size = document.createElement("span");
        size.textContent = file.size ? `${(file.size / 1024 / 1024).toFixed(1)} MB ↗` : "Descargar ↗";
        link.append(name, size);
        assets.append(link);
      });
      status.textContent = "Archivos servidos directamente por GitHub Releases.";
    }
    if (release.html_url) {
      const notes = document.createElement("a");
      notes.className = "release-status";
      notes.href = release.html_url;
      notes.target = "_blank";
      notes.rel = "noopener";
      notes.textContent = "Leer notas de esta versión ↗";
      assets.append(notes);
    }
  } catch (error) {
    version.textContent = "No se pudo consultar GitHub";
    date.textContent = "Comprueba tu conexión e inténtalo de nuevo.";
    status.textContent = error.message;
  }
}

loadLatestRelease();