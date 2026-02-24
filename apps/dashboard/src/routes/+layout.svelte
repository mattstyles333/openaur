<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { Brain, Heart, Bot, Terminal, LayoutDashboard, RefreshCw, Settings, ExternalLink, Menu, X } from 'lucide-svelte';
	import { AlertCircle } from 'lucide-svelte';
	import { memoryStore, heartStore, agentsStore, sessionsStore, wsStore } from '$lib/stores';

	// Mobile menu state
	let mobileMenuOpen = $state(false);

	// Navigation items
	const navItems = [
		{ path: '/', label: 'Overview', icon: LayoutDashboard },
		{ path: '/memory', label: 'Memory', icon: Brain },
		{ path: '/heart', label: 'Heart', icon: Heart },
		{ path: '/agents', label: 'Agents', icon: Bot },
		{ path: '/sessions', label: 'Sessions', icon: Terminal },
		{ path: '/config', label: 'Settings', icon: Settings }
	];

	const externalLinks = [
		{ url: 'http://localhost:3000', label: 'Open WebUI ↗', icon: ExternalLink },
		{ url: 'http://localhost:8000/docs', label: 'API Docs ↗', icon: ExternalLink },
	];

	// Check for any errors
	const hasErrors = $derived(
		$memoryStore.error || $heartStore.error || $agentsStore.error || $sessionsStore.error
	);

	// Manual refresh button (HTTP fallback when WebSocket fails)
	function refreshAll() {
		memoryStore.refresh(false);
		heartStore.refresh(false);
		agentsStore.refresh(false);
		sessionsStore.refresh(false);
	}

	// WebSocket-only - no polling
	$effect(() => {
		wsStore.connect();
		
		// Initial data fetch on mount
		memoryStore.refresh(false);
		heartStore.refresh(false);
		agentsStore.refresh(false);
		sessionsStore.refresh(false);
		
		return () => wsStore.disconnect();
	});

	let { children } = $props();
</script>

<div class="min-h-screen bg-deep-dark flex">
	<!-- Mobile Header -->
	<div class="lg:hidden fixed top-0 left-0 right-0 h-16 bg-card-bg border-b border-border-subtle z-50 flex items-center justify-between px-4">
		<h1 class="text-xl font-bold gradient-text">OpenAur</h1>
		<button
			onclick={() => mobileMenuOpen = !mobileMenuOpen}
			class="p-2 rounded-lg hover:bg-card-hover text-text-primary"
		>
			{#if mobileMenuOpen}
				<X size={24} />
			{:else}
				<Menu size={24} />
			{/if}
		</button>
	</div>

	<!-- Sidebar -->
	<aside class="w-64 bg-card-bg border-r border-border-subtle flex flex-col fixed lg:static h-full z-40 transition-transform duration-300 {mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} lg:translate-x-0">
		<!-- Logo -->
		<div class="p-6 border-b border-border-subtle">
			<h1 class="text-xl font-bold gradient-text tracking-tight">OpenAur</h1>
			<p class="text-xs text-text-secondary mt-1">Dashboard</p>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 p-4 space-y-2">
			{#each navItems as item}
				<a
					href={item.path}
					onclick={() => mobileMenuOpen = false}
					class="flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 {$page.url.pathname === item.path ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30' : 'text-text-secondary hover:text-text-primary hover:bg-card-hover'}"
				>
					<svelte:component this={item.icon} size={20} />
					<span class="font-medium">{item.label}</span>
				</a>
			{/each}
		</nav>

		<!-- External Links -->
		<div class="p-4 border-t border-border-subtle space-y-2">
			<p class="text-xs text-text-secondary mb-2">External Services</p>
			{#each externalLinks as link}
				<a
					href={link.url}
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-3 px-4 py-2 rounded-lg text-text-secondary hover:text-neon-cyan hover:bg-card-hover transition-all"
				>
					<svelte:component this={link.icon} size={18} />
					<span class="text-sm font-medium">{link.label}</span>
				</a>
			{/each}
		</div>

		<!-- Refresh button -->
		<div class="p-4 border-t border-border-subtle">
			<button
				onclick={refreshAll}
				class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-card-hover text-text-secondary hover:text-neon-cyan transition-colors"
			>
				<RefreshCw size={16} />
				<span class="text-sm">Manual Refresh</span>
			</button>
		</div>
	</aside>

	<!-- Mobile Overlay -->
	{#if mobileMenuOpen}
		<div 
			class="fixed inset-0 bg-black/50 z-30 lg:hidden"
			onclick={() => mobileMenuOpen = false}
		></div>
	{/if}

	<!-- Main content -->
	<main class="flex-1 overflow-auto lg:pt-0 pt-16">
		<!-- Error Banner -->
		{#if hasErrors}
			<div class="p-4 bg-neon-red/10 border-b border-neon-red/30">
				<div class="flex items-center gap-2 text-neon-red mb-2">
					<AlertCircle size={18} />
					<span class="font-medium">Connection Error</span>
				</div>
				{#if $memoryStore.error}
					<p class="text-sm text-text-secondary">Memory: {$memoryStore.error}</p>
				{/if}
				{#if $heartStore.error}
					<p class="text-sm text-text-secondary">Heart: {$heartStore.error}</p>
				{/if}
				<button 
					onclick={refreshAll}
					class="mt-2 text-sm text-neon-cyan hover:underline"
				>
					Click to retry
				</button>
			</div>
		{/if}
		
		{@render children()}
	</main>
</div>
