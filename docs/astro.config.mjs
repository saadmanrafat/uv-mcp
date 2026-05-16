import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const prod = process.env.NODE_ENV === 'production';

export default defineConfig({
	site: 'https://saadman.dev',
	base: '/uv-mcp',
	integrations: [
		starlight({
			title: 'UV-MCP',
			components: {
				Footer: './src/components/Footer.astro',
			},
			description:
				'UV-MCP is a Model Context Protocol (MCP) server that exposes 45 typed tools for uv, the extremely fast Python package manager. Built by Saadman Rafat (saadman.dev).'
			favicon: '/favicon.svg',
			head: [
				{
					tag: 'meta',
					attrs: { property: 'og:type', content: 'website' },
				},
				{
					tag: 'meta',
					attrs: { property: 'og:site_name', content: 'UV-MCP' },
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image',
						content: 'https://saadman.dev/uv-mcp/og-image.png',
					},
				},
				{
					tag: 'meta',
					attrs: { name: 'twitter:card', content: 'summary_large_image' },
				},
				{
					tag: 'meta',
					attrs: { name: 'twitter:creator', content: '@saadmanrafat_' },
				},
				{
					tag: 'meta',
					attrs: { name: 'twitter:title', content: 'UV-MCP — Stop Shop for Python Environment Management' },
				},
				{
					tag: 'meta',
					attrs: { name: 'twitter:description', content: '45 typed MCP tools covering 100% of the uv CLI surface area. Built by Saadman Rafat.' },
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:image',
						content: 'https://saadman.dev/uv-mcp/og-image.png',
					},
				},
				{
					tag: 'link',
					attrs: { rel: 'canonical', href: 'https://saadman.dev/uv-mcp/' },
				},
			],
			// Social links intentionally omitted for a minimalist header
			sidebar: [
				{
					label: 'Guides',
					items: [
						{ label: 'Introduction', link: '/guides/introduction/' },
						{ label: 'Installation', link: '/guides/installation/' },
						{ label: 'Usage', link: '/guides/usage/' },
					],
				},
				{
					label: 'Concepts',
					items: [
						{ label: 'MCP and Extensions', link: '/guides/concepts/mcp-and-extensions/' },
					],
				},
				{
					label: 'Development',
					items: [
						{ label: 'Architecture', link: '/guides/architecture/' },
						{ label: 'Contributing', link: '/guides/contributing/' },
					],
				},
				{
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
		}),
	],
});
