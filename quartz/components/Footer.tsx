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
        <p>cultivado con ❤️ por <a href="https://github.com/matzalazar">matzalazar</a></p>
        <p>¿querés replicar esto? <a href="mailto:matias.zalazar@icloud.com">escribime</a></p>
      </footer>
    )
  }

  Footer.css = style
  return Footer
}) satisfies QuartzComponentConstructor
