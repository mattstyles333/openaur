<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { Brain, Heart, Bot, Terminal, LayoutDashboard, RefreshCw } from 'lucide-svelte';
	import { memoryStore, heartStore, agentsStore, sessionsStore, createAutoRefresh } from '$lib/stores';

	const navItems = [
		{ path: '/', label: 'Overview', icon: LayoutDashboard },
		{ path: '/memory', label: 'Memory', icon: Brain },
		{ path: '/agents', label: 'Agents', icon: Bot },
		{ path: '/sessions', label: 'Sessions', icon: Terminal },
		{ path: '/heart', label: 'Heart', icon: Heart }
	];

	// Auto-refresh all stores every 5 seconds
	const autoRefresh = createAutoRefresh(5000);
	
	function refreshAll() {
		memoryStore.refresh();
		heartStore.refresh();
		agentsStore.refresh();
		sessionsStore.refresh();
	}

	// Start auto-refresh on mount
	$effect(() => {
		refreshAll();
		autoRefresh.start(refreshAll);
		return () => autoRefresh.stop();
	});

	let { children } = $props();
</script>

<div class="min-h-screen bg-deep-dark flex">
	<!-- Sidebar -->
	<aside class="w-64 bg-card-bg border-r border-border-subtle flex flex-col">
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
					class="flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 {$page.url.pathname === item.path ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30' : 'text-text-secondary hover:text-text-primary hover:bg-card-hover'}"
				>
					<svelte:component this={item.icon} size={20} />
					<span class="font-medium">{item.label}</span>
				</a>
			{/each}
		</nav>

		<!-- Refresh button -->
		<div class="p-4 border-t border-border-subtle">
			<button
				onclick={refreshAll}
				class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-card-hover text-text-secondary hover:text-neon-cyan transition-colors"
			>
				<RefreshCw size={16} />
				<span class="text-sm">Refresh Data</span>
			</button>
		</div>
	</aside>

	<!-- Main content -->
	<main class="flex-1 overflow-auto">
		{@render children()}
	</main>
</div>
