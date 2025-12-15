// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://saadman.dev',
	base: '/uv-mcp',
	integrations: [
		starlight({
			title: 'UV-MCP',
			social: [
				{
					icon: 'github',
					href: 'https://github.com/saadmanrafat/uv-mcp',
					label: 'GitHub',
				},
			],
			sidebar: [
				{
					label: 'Guides',
					items: [
						// Each item here is one entry in the navigation menu.
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