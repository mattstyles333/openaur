<script lang="ts">
	import { memoryStore } from '$lib/stores';
	import { Brain, Search, Trash2, Tag } from 'lucide-svelte';
	import { api } from '$lib/api';
	import type { Memory } from '$lib/api';

	let searchQuery = $state('');
	let filteredMemories = $state<Memory[]>([]);
	let searchLoading = $state(false);

	async function handleSearch() {
		if (!searchQuery.trim()) {
			filteredMemories = [];
			return;
		}
		searchLoading = true;
		try {
			filteredMemories = await api.searchMemories(searchQuery, 50);
		} finally {
			searchLoading = false;
		}
	}

	const displayedMemories = $derived(
		searchQuery.trim() ? filteredMemories : $memoryStore.memories
	);

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleString();
	}

	function getTypeColor(type: string): string {
		const colors: Record<string, string> = {
			'user_query': 'text-neon-cyan',
			'assistant_response': 'text-neon-purple',
			'action_learning': 'text-neon-green',
			'system': 'text-neon-yellow'
		};
		return colors[type] || 'text-text-secondary';
	}

	function getTypeBg(type: string): string {
		const bgs: Record<string, string> = {
			'user_query': 'bg-neon-cyan/10',
			'assistant_response': 'bg-neon-purple/10',
			'action_learning': 'bg-neon-green/10',
			'system': 'bg-neon-yellow/10'
		};
		return bgs[type] || 'bg-card-hover';
	}
</script>

<svelte:head>
	<title>Memory Browser | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<header class="mb-8">
		<div class="flex items-center gap-3 mb-2">
			<Brain class="text-neon-cyan" size={28} />
			<h1 class="text-3xl font-bold text-text-primary">Memory Browser</h1>
		</div>
		<p class="text-text-secondary">Search and explore stored memories</p>
	</header>

	<!-- Search Bar -->
	<div class="mb-8">
		<div class="relative max-w-2xl">
			<Search class="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary" size={20} />
			<input
				type="text"
				bind:value={searchQuery}
				oninput={handleSearch}
				placeholder="Search memories..."
				class="w-full pl-12 pr-4 py-3 bg-card-bg border border-border-subtle rounded-xl text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-neon-cyan focus:ring-1 focus:ring-neon-cyan transition-all"
			/>
		</div>
	</div>

	<!-- Memory Architecture Stats -->
	{#if $memoryStore.stats}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
			<!-- Short-term (Working Memory) -->
			<div class="bg-card-bg rounded-lg p-6 border border-border-subtle glow-border">
				<div class="flex items-center gap-3 mb-4">
					<div class="p-2 bg-neon-cyan/10 rounded-lg">
						<Brain class="text-neon-cyan" size={20} />
					</div>
					<div>
						<p class="text-text-primary font-semibold">Working Memory</p>
						<p class="text-text-secondary text-xs">Hot cache - instant access</p>
					</div>
				</div>
				<div class="flex items-end justify-between mb-2">
					<p class="text-3xl font-bold text-neon-cyan">{$memoryStore.stats.short_term || 0}</p>
					<p class="text-text-secondary text-sm">/ {$memoryStore.stats.short_term_max || 30}</p>
				</div>
				<div class="h-2 bg-deep-dark rounded-full overflow-hidden">
					<div 
						class="h-full bg-neon-cyan rounded-full transition-all duration-500"
						style="width: {(($memoryStore.stats.short_term || 0) / ($memoryStore.stats.short_term_max || 30)) * 100}%"
					></div>
				</div>
			</div>
			
			<!-- Long-term (Persistent Storage) -->
			<div class="bg-card-bg rounded-lg p-6 border border-border-subtle">
				<div class="flex items-center gap-3 mb-4">
					<div class="p-2 bg-neon-purple/10 rounded-lg">
						<Brain class="text-neon-purple" size={20} />
					</div>
					<div>
						<p class="text-text-primary font-semibold">Long-term Storage</p>
						<p class="text-text-secondary text-xs">SQLite database - persistent</p>
					</div>
				</div>
				<div class="flex items-end justify-between mb-2">
					<p class="text-3xl font-bold text-neon-purple">{$memoryStore.stats.long_term || 0}</p>
					<p class="text-text-secondary text-sm">memories</p>
				</div>
				<div class="h-2 bg-deep-dark rounded-full overflow-hidden">
					<div class="h-full bg-neon-purple/50 rounded-full"></div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Memory Types -->
	{#if $memoryStore.stats && Object.keys($memoryStore.stats.by_type).length > 0}
		<div class="mb-8 flex flex-wrap gap-2">
			{#each Object.entries($memoryStore.stats.by_type) as [type, count]}
				<div class="px-3 py-1.5 rounded-full bg-card-bg border border-border-subtle text-sm">
					<span class="text-text-secondary">{type}:</span>
					<span class="text-neon-cyan font-medium ml-1">{count}</span>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Memories List -->
	<div class="bg-card-bg rounded-xl border border-border-subtle overflow-hidden">
		{#if $memoryStore.loading || searchLoading}
			<div class="p-12 text-center">
				<div class="animate-spin inline-block w-8 h-8 border-2 border-neon-cyan border-t-transparent rounded-full mb-4"></div>
				<p class="text-text-secondary">Loading memories...</p>
			</div>
		{:else if displayedMemories.length === 0}
			<div class="p-12 text-center">
				<Brain size={48} class="text-text-secondary mx-auto mb-4" />
				<p class="text-text-secondary text-lg">
					{searchQuery ? 'No memories found matching your search.' : 'No memories yet.'}
				</p>
			</div>
		{:else}
			<div class="divide-y divide-border-subtle">
				{#each displayedMemories as memory (memory.id)}
					<div class="p-6 hover:bg-card-hover transition-colors">
						<div class="flex items-start gap-4">
							<div class="flex-shrink-0">
								<span class="px-3 py-1 text-xs font-medium rounded-full {getTypeBg(memory.memory_type)} {getTypeColor(memory.memory_type)}">
									{memory.memory_type}
								</span>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-text-primary leading-relaxed mb-3">{memory.content}</p>
								<div class="flex flex-wrap items-center gap-4 text-sm">
									<div class="flex items-center gap-1 text-text-secondary">
										<Tag size={14} />
										<span>{memory.tags.join(', ') || 'No tags'}</span>
									</div>
									<div class="text-text-secondary">
										Importance: <span class="text-neon-cyan">{memory.importance.toFixed(2)}</span>
									</div>
									<div class="text-text-secondary">
										{formatDate(memory.created_at)}
									</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
