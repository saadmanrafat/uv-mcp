import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

const prod = process.env.NODE_ENV === "production";

export default defineConfig({
  site: "https://saadman.dev",
  base: "/uv-mcp",
  integrations: [
    starlight({
      title: "uv-mcp",
      components: {
        Footer: "./src/components/Footer.astro",
      },
      description:
        "uv-mcp is the Model Context Protocol (MCP) server for uv: it gives Claude, Codex, Gemini and any MCP agent the full uv toolchain as safe, typed tools. Built by Saadman Rafat (saadman.dev).",
      favicon: "/favicon.svg",
      head: [
        {
          tag: "meta",
          attrs: { property: "og:type", content: "website" },
        },
        {
          tag: "meta",
          attrs: { property: "og:site_name", content: "uv-mcp" },
        },
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: "https://saadman.dev/uv-mcp/og-image.png",
          },
        },
        {
          tag: "meta",
          attrs: { name: "twitter:card", content: "summary_large_image" },
        },
        {
          tag: "meta",
          attrs: { name: "twitter:creator", content: "@saadmanrafat_" },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:title",
            content: "uv-mcp: the full uv toolchain for AI coding agents",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:description",
            content:
              "Projects, dependencies, Python versions, virtual environments and tools for Claude, Codex and Gemini. One command: uvx uv-mcp-server.",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:image",
            content: "https://saadman.dev/uv-mcp/og-image.png",
          },
        },
        {
          tag: "link",
          attrs: { rel: "canonical", href: "https://saadman.dev/uv-mcp/" },
        },
      ],
      // Social links intentionally omitted for a minimalist header
      sidebar: [
        {
          label: "Guides",
          items: [
            { label: "Introduction", link: "/guides/introduction/" },
            { label: "Installation", link: "/guides/installation/" },
            { label: "Usage", link: "/guides/usage/" },
            { label: "Configuration", link: "/guides/configuration/" },
            { label: "Security", link: "/guides/security/" },
            { label: "Troubleshooting", link: "/guides/troubleshooting/" },
          ],
        },
        {
          label: "Concepts",
          items: [
            {
              label: "MCP and Extensions",
              link: "/guides/concepts/mcp-and-extensions/",
            },
          ],
        },
        {
          label: "Development",
          items: [
            { label: "Architecture", link: "/guides/architecture/" },
            { label: "Contributing", link: "/guides/contributing/" },
            { label: "Changelog", link: "/guides/changelog/" },
          ],
        },
        {
          label: "Reference",
          autogenerate: { directory: "reference" },
        },
      ],
    }),
  ],
});
