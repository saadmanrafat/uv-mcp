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
				'UV-MCP is a Model Context Protocol (MCP) server that exposes 46 typed tools for uv, the extremely fast Python package manager. Built by Saadman Rafat (saadman.dev).',
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
						content: 'https://saadman.dev/uv-mcp/og-image.svg',
					},
				},
				{
					tag: 'meta',
					attrs: { property: 'twitter:card', content: 'summary_large_image' },
				},
				{
					tag: 'meta',
					attrs: { property: 'twitter:creator', content: '@saadmanrafat' },
				},
				{
					tag: 'meta',
					attrs: {
						property: 'twitter:image',
						content: 'https://saadman.dev/uv-mcp/og-image.svg',
					},
				},
				{
					tag: 'link',
					attrs: { rel: 'canonical', href: 'https://saadman.dev/uv-mcp/' },
				},
			],
			social: [
				{
					icon: 'github',
					href: 'https://github.com/saadmanrafat/uv-mcp',
					label: 'GitHub',
				},
				{
					icon: 'twitter',
					href: 'https://twitter.com/saadmanrafat',
					label: 'Twitter',
				},
				{
					icon: 'linkedin',
					href: 'https://linkedin.com/in/saadmanrafat',
					label: 'LinkedIn',
				},
			],
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