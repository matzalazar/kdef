import { QuartzTransformerPlugin } from "../types"
import { Root as MdRoot } from "mdast"
import { toString } from "mdast-util-to-string"

export interface NovedadSemana {
  semana: string
  entradas: string[]
}

export const NovedadesParser: QuartzTransformerPlugin = () => {
  return {
    name: "NovedadesParser",
    markdownPlugins() {
      return [
        () =>
          (tree: MdRoot, file) => {
            if (file.stem !== "novedades") return

            const semanas: NovedadSemana[] = []
            let current: NovedadSemana | null = null

            for (const node of tree.children) {
              if (node.type === "heading" && node.depth === 2) {
                if (current) semanas.push(current)
                current = { semana: toString(node), entradas: [] }
              } else if (node.type === "list" && current) {
                for (const item of node.children) {
                  current.entradas.push(toString(item))
                }
              }
            }

            if (current) semanas.push(current)
            file.data.novedades = semanas
          },
      ]
    },
  }
}

declare module "vfile" {
  interface DataMap {
    novedades: NovedadSemana[]
  }
}
