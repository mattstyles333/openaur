<script lang="ts">
	import { memoryStore } from '$lib/stores';
	import { Brain, Search, Trash2, Tag, Filter, Download, Upload, X } from 'lucide-svelte';
	import { api } from '$lib/api';
	import type { Memory } from '$lib/api';

	let searchQuery = $state('');
	let filteredMemories = $state<Memory[]>([]);
	let searchLoading = $state(false);
	let selectedType = $state<string>('all');
	let selectedTag = $state<string>('all');
	let showImportModal = $state(false);
	let showExportModal = $state(false);
	let importContent = $state('');
	let newTagInput = $state('');
	let editingMemory = $state<string | null>(null);
	let editTags = $state<string[]>([]);

	const memoryTypes = ['all', 'user_query', 'assistant_response', 'action_learning', 'system'];

	// Get all unique tags from memories
	const allTags = $derived(() => {
		const tags = new Set<string>();
		$memoryStore.memories.forEach(m => {
			(m.tags || []).forEach(t => tags.add(t));
		});
		return ['all', ...Array.from(tags).sort()];
	});

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

	// Filter memories based on type and tag
	const filteredByTypeAndTag = $derived(() => {
		let memories = searchQuery.trim() ? filteredMemories : $memoryStore.memories;
		
		if (selectedType !== 'all') {
			memories = memories.filter(m => m.memory_type === selectedType);
		}
		
		if (selectedTag !== 'all') {
			memories = memories.filter(m => (m.tags || []).includes(selectedTag));
		}
		
		return memories;
	});

	const displayedMemories = $derived(filteredByTypeAndTag());

	function formatDate(dateStr: string): string {
		if (!dateStr) return 'Unknown date';
		try {
			const date = new Date(dateStr);
			if (isNaN(date.getTime())) return 'Unknown date';
			return date.toLocaleString();
		} catch {
			return 'Unknown date';
		}
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

	async function deleteMemory(id: string) {
		if (!confirm('Are you sure you want to delete this memory?')) return;
		try {
			await api.deleteMemory(id);
			await memoryStore.refresh();
		} catch (e) {
			console.error('Failed to delete memory:', e);
		}
	}

	async function startEditing(memory: Memory) {
		editingMemory = memory.id;
		editTags = [...(memory.tags || [])];
	}

	async function saveTags(memoryId: string) {
		try {
			await api.updateMemoryTags(memoryId, editTags);
			editingMemory = null;
			await memoryStore.refresh();
		} catch (e) {
			console.error('Failed to update tags:', e);
		}
	}

	function addTag() {
		if (newTagInput.trim() && !editTags.includes(newTagInput.trim())) {
			editTags = [...editTags, newTagInput.trim()];
			newTagInput = '';
		}
	}

	function removeTag(tag: string) {
		editTags = editTags.filter(t => t !== tag);
	}

	async function exportMemories() {
		const data = {
			memories: $memoryStore.memories,
			exported_at: new Date().toISOString(),
			version: '1.0'
		};
		const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `openaur-memories-${new Date().toISOString().split('T')[0]}.json`;
		a.click();
		URL.revokeObjectURL(url);
		showExportModal = false;
	}

	async function importMemories() {
		try {
			const data = JSON.parse(importContent);
			if (data.memories && Array.isArray(data.memories)) {
				for (const memory of data.memories) {
					await api.storeMemory({
						content: memory.content,
						source: memory.source || 'import',
						tags: memory.tags || []
					});
				}
				await memoryStore.refresh();
				showImportModal = false;
				importContent = '';
				alert(`Imported ${data.memories.length} memories`);
			}
		} catch (e) {
			alert('Invalid JSON format');
		}
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
		<p class="text-text-secondary">Search, filter, and manage stored memories</p>
	</header>

	<!-- Search and Filter Bar -->
	<div class="mb-8 space-y-4">
		<!-- Search -->
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

		<!-- Filters -->
		<div class="flex flex-wrap items-center gap-4">
			<div class="flex items-center gap-2">
				<Filter size={16} class="text-text-secondary" />
				<select
					bind:value={selectedType}
					class="px-3 py-2 bg-card-bg border border-border-subtle rounded-lg text-text-primary text-sm focus:outline-none focus:border-neon-cyan"
				>
					<option value="all">All Types</option>
					<option value="user_query">User Query</option>
					<option value="assistant_response">Assistant Response</option>
					<option value="action_learning">Action Learning</option>
					<option value="system">System</option>
				</select>
			</div>

			<div class="flex items-center gap-2">
				<Tag size={16} class="text-text-secondary" />
				<select
					bind:value={selectedTag}
					class="px-3 py-2 bg-card-bg border border-border-subtle rounded-lg text-text-primary text-sm focus:outline-none focus:border-neon-cyan"
				>
					<option value="all">All Tags</option>
					{#each allTags().slice(1) as tag}
						<option value={tag}>{tag}</option>
					{/each}
				</select>
			</div>

			<!-- Import/Export Buttons -->
			<div class="flex items-center gap-2 ml-auto">
				<button
					onclick={() => showExportModal = true}
					class="flex items-center gap-2 px-3 py-2 bg-card-bg border border-border-subtle rounded-lg text-text-secondary hover:text-neon-cyan hover:border-neon-cyan transition-all text-sm"
				>
					<Download size={16} />
					Export
				</button>
				<button
					onclick={() => showImportModal = true}
					class="flex items-center gap-2 px-3 py-2 bg-card-bg border border-border-subtle rounded-lg text-text-secondary hover:text-neon-cyan hover:border-neon-cyan transition-all text-sm"
				>
					<Upload size={16} />
					Import
				</button>
			</div>
		</div>

		<!-- Active Filters Display -->
		{#if selectedType !== 'all' || selectedTag !== 'all'}
			<div class="flex items-center gap-2 text-sm">
				<span class="text-text-secondary">Active filters:</span>
				{#if selectedType !== 'all'}
					<span class="px-2 py-1 bg-neon-cyan/10 text-neon-cyan rounded-full text-xs">
						Type: {selectedType}
						<button class="ml-1 hover:text-white" onclick={() => selectedType = 'all'}>×</button>
					</span>
				{/if}
				{#if selectedTag !== 'all'}
					<span class="px-2 py-1 bg-neon-purple/10 text-neon-purple rounded-full text-xs">
						Tag: {selectedTag}
						<button class="ml-1 hover:text-white" onclick={() => selectedTag = 'all'}>×</button>
					</span>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Memory Stats -->
	{#if $memoryStore.stats}
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle mb-8">
			<div class="flex items-center justify-between mb-4">
				<div class="flex items-center gap-3">
					<div class="p-2 bg-neon-cyan/10 rounded-lg">
						<Brain class="text-neon-cyan" size={20} />
					</div>
					<div>
						<p class="text-text-primary font-semibold">Total Memories</p>
						<p class="text-text-secondary text-xs">Stored in SQLite with HMD2 architecture</p>
					</div>
				</div>
				<div class="text-right">
					<p class="text-3xl font-bold text-neon-cyan">{$memoryStore.stats.total_memories}</p>
					<p class="text-xs text-text-secondary">Backend: {$memoryStore.stats.backend || 'sqlite'}</p>
				</div>
			</div>
			
			{#if Object.keys($memoryStore.stats.by_type || {}).length > 0}
				<div class="flex flex-wrap gap-2 mt-4">
					{#each Object.entries($memoryStore.stats.by_type) as [type, count]}
						<div class="px-3 py-1.5 rounded-full bg-deep-dark border border-border-subtle text-sm cursor-pointer hover:border-neon-cyan transition-all {selectedType === type ? 'border-neon-cyan bg-neon-cyan/10' : ''}"
							onclick={() => selectedType = selectedType === type ? 'all' : type}>
							<span class="text-text-secondary">{type}:</span>
							<span class="text-neon-cyan font-medium ml-1">{count}</span>
						</div>
					{/each}
				</div>
			{/if}
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
					{searchQuery || selectedType !== 'all' || selectedTag !== 'all' 
						? 'No memories found matching your filters.' 
						: 'No memories yet.'}
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
								
								<!-- Tags Editing -->
								{#if editingMemory === memory.id}
									<div class="mb-3 p-3 bg-deep-dark rounded-lg">
										<div class="flex flex-wrap gap-2 mb-2">
											{#each editTags as tag}
												<span class="px-2 py-1 bg-neon-cyan/20 text-neon-cyan rounded-full text-xs flex items-center gap-1">
													{tag}
													<button onclick={() => removeTag(tag)} class="hover:text-white">×</button>
												</span>
											{/each}
										</div>
										<div class="flex gap-2">
											<input
												type="text"
												bind:value={newTagInput}
												placeholder="Add tag..."
												class="flex-1 px-3 py-1.5 bg-card-bg border border-border-subtle rounded text-text-primary text-sm focus:outline-none focus:border-neon-cyan"
												onkeydown={(e) => e.key === 'Enter' && addTag()}
											/>
											<button
												onclick={addTag}
												class="px-3 py-1.5 bg-neon-cyan text-black rounded text-sm font-medium hover:bg-neon-cyan/80 transition-colors"
											>
												Add
											</button>
											<button
												onclick={() => saveTags(memory.id)}
												class="px-3 py-1.5 bg-neon-green text-black rounded text-sm font-medium hover:bg-neon-green/80 transition-colors"
											>
												Save
											</button>
											<button
												onclick={() => editingMemory = null}
												class="px-3 py-1.5 bg-border-subtle text-text-primary rounded text-sm hover:bg-card-hover transition-colors"
											>
												Cancel
											</button>
										</div>
									</div>
								{:else}
									<div class="flex flex-wrap items-center gap-4 text-sm">
										<div class="flex items-center gap-1 text-text-secondary">
											<Tag size={14} />
											<span class="flex gap-1">
												{#if memory.tags && memory.tags.length > 0}
													{#each memory.tags as tag}
														<span class="px-2 py-0.5 bg-neon-cyan/10 text-neon-cyan rounded text-xs cursor-pointer hover:bg-neon-cyan/20"
															onclick={() => selectedTag = tag}>
															{tag}
														</span>
													{/each}
												{:else}
													<span class="text-text-secondary/50 italic">No tags</span>
												{/if}
											</span>
										</div>
										<div class="text-text-secondary">
											Importance: <span class="text-neon-cyan">{(memory.importance || 0).toFixed(2)}</span>
										</div>
										<div class="text-text-secondary">
											{formatDate(memory.created_at)}
										</div>
									</div>
								{/if}
							</div>
							<div class="flex-shrink-0 flex items-center gap-2">
								<button
									onclick={() => startEditing(memory)}
									class="p-2 text-text-secondary hover:text-neon-cyan hover:bg-neon-cyan/10 rounded-lg transition-all"
									title="Edit tags"
								>
									<Tag size={16} />
								</button>
								<button
									onclick={() => deleteMemory(memory.id)}
									class="p-2 text-text-secondary hover:text-neon-red hover:bg-neon-red/10 rounded-lg transition-all"
									title="Delete memory"
								>
									<Trash2 size={16} />
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<!-- Import Modal -->
{#if showImportModal}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
		<div class="bg-card-bg rounded-xl border border-border-subtle max-w-lg w-full p-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-text-primary">Import Memories</h2>
				<button onclick={() => showImportModal = false} class="text-text-secondary hover:text-white">
					<X size={20} />
				</button>
			</div>
			<p class="text-text-secondary text-sm mb-4">Paste JSON export data below:</p>
			<textarea
				bind:value={importContent}
				class="w-full h-48 px-4 py-3 bg-deep-dark border border-border-subtle rounded-lg text-text-primary text-sm font-mono focus:outline-none focus:border-neon-cyan resize-none"
				placeholder="Paste exported JSON here..."
			></textarea>
			<div class="flex justify-end gap-2 mt-4">
				<button
					onclick={() => showImportModal = false}
					class="px-4 py-2 text-text-secondary hover:text-white transition-colors"
				>
					Cancel
				</button>
				<button
					onclick={importMemories}
					class="px-4 py-2 bg-neon-cyan text-black rounded-lg font-medium hover:bg-neon-cyan/80 transition-colors"
				>
					Import
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Export Modal -->
{#if showExportModal}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
		<div class="bg-card-bg rounded-xl border border-border-subtle max-w-sm w-full p-6 text-center">
			<Download size={48} class="text-neon-cyan mx-auto mb-4" />
			<h2 class="text-xl font-bold text-text-primary mb-2">Export Memories</h2>
			<p class="text-text-secondary text-sm mb-6">
				Export {$memoryStore.memories.length} memories to JSON file?
			</p>
			<div class="flex justify-center gap-2">
				<button
					onclick={() => showExportModal = false}
					class="px-4 py-2 text-text-secondary hover:text-white transition-colors"
				>
					Cancel
				</button>
				<button
					onclick={exportMemories}
					class="px-4 py-2 bg-neon-cyan text-black rounded-lg font-medium hover:bg-neon-cyan/80 transition-colors"
				>
					Download
				</button>
			</div>
		</div>
	</div>
{/if}
