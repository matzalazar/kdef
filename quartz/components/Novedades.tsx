import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { resolveRelative } from "../util/path"
import { classNames } from "../util/lang"
import style from "./styles/novedades.scss"
import { NovedadSemana } from "../plugins/transformers/novedades"

export default (() => {
  const Novedades: QuartzComponent = ({ allFiles, fileData, displayClass }: QuartzComponentProps) => {
    const novedadesFile = allFiles.find((f) => f.slug === "novedades")
    const semanas = (novedadesFile?.novedades ?? []) as NovedadSemana[]

    if (semanas.length === 0) return null

    return (
      <div class={classNames(displayClass, "novedades")}>
        <h3>Novedades</h3>
        {semanas.map((s) => (
          <div class="novedades-semana">
            <h4>{s.semana}</h4>
            <ul>
              {s.entradas.map((e) => (
                <li>{e}</li>
              ))}
            </ul>
          </div>
        ))}
        {novedadesFile?.slug && (
          <p class="novedades-link">
            <a href={resolveRelative(fileData.slug!, novedadesFile.slug)} class="internal">
              Ver todas →
            </a>
          </p>
        )}
      </div>
    )
  }

  Novedades.css = style
  return Novedades
}) satisfies QuartzComponentConstructor
