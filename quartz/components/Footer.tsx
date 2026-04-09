import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import style from "./styles/footer.scss"

interface Options {
  links: Record<string, string>
}

export default ((opts?: Options) => {
  const Footer: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    const links = Object.entries(opts?.links ?? {})
    return (
      <footer class={`${displayClass ?? ""}`}>
        <p>
          creado con ❤️ por matzalazar
          {links.map(([text, link]) => (
            <span key={link}>
              {" - "}
              <a href={link}>{text.toLowerCase()}</a>
            </span>
          ))}
        </p>
        <p>si querés un jardín digital para tu carrera, <a href="mailto:matias.zalazar@icloud.com">me podés escribir</a> :)</p>
      </footer>
    )
  }

  Footer.css = style
  return Footer
}) satisfies QuartzComponentConstructor
