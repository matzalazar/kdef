import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import style from "./styles/footer.scss"

interface Options {
  links?: Record<string, string>
}

export default ((_opts?: Options) => {
  const Footer: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <footer class={`${displayClass ?? ""}`}>
        <p>cultivado con ❤️ por <a href="https://matzalazar.com">matzalazar</a></p>
        <p dangerouslySetInnerHTML={{__html: '¿querés replicar esto? <!-- email_off --><a href="mailto:contacto@matzalazar.com">escribime</a><!-- /email_off -->'}}></p>
      </footer>
    )
  }

  Footer.css = style
  return Footer
}) satisfies QuartzComponentConstructor
