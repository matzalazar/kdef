import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * kdef — Jardín de conocimiento para la Licenciatura en Ciberdefensa (UNDEF)
 * Recurso estudiantil independiente. No oficial.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "kdef",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "es-AR",
    baseUrl: "kdef.com.ar",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      // Fuentes locales/sistema — sin dependencias externas de red
      fontOrigin: "local",
      cdnCaching: false,
      typography: {
        header: "JetBrains Mono",
        body: "JetBrains Mono",
        code: "JetBrains Mono",
      },
      colors: {
        // Paleta terminal: dark por defecto + light funcional
        lightMode: {
          light: "#f7f7f7",
          lightgray: "#e5e5e5",
          gray: "#6b6b6b",
          darkgray: "#111111",
          dark: "#007a2b",
          secondary: "#00661f",
          tertiary: "#007a2b",
          highlight: "rgba(0, 122, 43, 0.08)",
          textHighlight: "rgba(0, 122, 43, 0.2)",
        },
        darkMode: {
          light: "#0d0d0d",
          lightgray: "#1a1a1a",
          gray: "#333333",
          darkgray: "#b0b0b0",
          dark: "#00ff41",
          secondary: "#00cc33",
          tertiary: "#ffb000",
          highlight: "rgba(0, 255, 65, 0.08)",
          textHighlight: "rgba(0, 255, 65, 0.25)",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-dark",
          dark: "github-dark",
        },
        keepBackground: true,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.Latex({ renderEngine: "katex" }),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "relative" }),
      Plugin.Description(),
      Plugin.NovedadesParser(),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
