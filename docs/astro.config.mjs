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
					link: 'https://github.com/saadmanrafat/uv-mcp',
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
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
		}),
	],
});