<script lang="ts">
	import { memoryStore, heartStore, agentsStore, sessionsStore } from '$lib/stores';
	import { Activity, Brain, Bot, Terminal, Zap, Heart, Cpu, Clock } from 'lucide-svelte';

	// Memory utilization percentage
	const memoryUtilization = $derived(
		$memoryStore.stats ? ($memoryStore.stats.utilization * 100).toFixed(1) : '0.0'
	);

	// Active agents count
	const activeAgents = $derived(
		$agentsStore.agents.filter(a => a.state === 'running').length
	);

	// Active sessions count
	const activeSessions = $derived(
		$sessionsStore.sessions.filter(s => s.status === 'active').length
	);
</script>

<svelte:head>
	<title>Overview | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<!-- Header -->
	<header class="mb-8">
		<h1 class="text-3xl font-bold text-text-primary mb-2">Dashboard Overview</h1>
		<p class="text-text-secondary">Real-time system monitoring and status</p>
	</header>

	<!-- Stats Grid -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
		<!-- Memory Card -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle glow-border card-hover">
			<div class="flex items-start justify-between mb-4">
				<div class="p-3 bg-neon-cyan/10 rounded-lg">
					<Brain class="text-neon-cyan" size={24} />
				</div>
				{#if $memoryStore.loading}
					<div class="animate-pulse w-2 h-2 bg-neon-cyan rounded-full"></div>
				{/if}
			</div>
			<div class="space-y-1">
				<p class="text-text-secondary text-sm">Total Memories</p>
				{#if $memoryStore.stats}
					<p class="text-2xl font-bold text-text-primary">{$memoryStore.stats.total_memories}</p>
					<p class="text-xs text-text-secondary">
						Backend: {$memoryStore.stats.backend || 'sqlite'}
					</p>
				{:else}
					<p class="text-2xl font-bold text-text-primary">-</p>
				{/if}
			</div>
			<!-- Progress bar -->
			{#if $memoryStore.stats}
				<div class="mt-4 h-2 bg-deep-dark rounded-full overflow-hidden">
					<div 
						class="h-full bg-gradient-to-r from-neon-cyan to-neon-purple rounded-full transition-all duration-500"
						style="width: {($memoryStore.stats.utilization * 100).toFixed(1)}%"
					></div>
				</div>
			{/if}
		</div>

		<!-- Heart Card -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle glow-border card-hover">
			<div class="flex items-start justify-between mb-4">
				<div class="p-3 bg-neon-red/10 rounded-lg heart-pulse">
					<Heart class="text-neon-red" size={24} />
				</div>
				{#if $heartStore.loading}
					<div class="animate-pulse w-2 h-2 bg-neon-red rounded-full"></div>
				{/if}
			</div>
			<div class="space-y-1">
				<p class="text-text-secondary text-sm">System Health</p>
				{#if $heartStore.status}
					<p class="text-2xl font-bold text-text-primary">{$heartStore.status.heart.physical.status}</p>
					<p class="text-xs text-text-secondary">
						Mood: {$heartStore.status.heart.emotional.mood}
					</p>
				{:else}
					<p class="text-2xl font-bold text-text-primary">-</p>
				{/if}
			</div>
		</div>

		<!-- Agents Card -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle glow-border card-hover">
			<div class="flex items-start justify-between mb-4">
				<div class="p-3 bg-neon-purple/10 rounded-lg">
					<Bot class="text-neon-purple" size={24} />
				</div>
				{#if $agentsStore.loading}
					<div class="animate-pulse w-2 h-2 bg-neon-purple rounded-full"></div>
				{/if}
			</div>
			<div class="space-y-1">
				<p class="text-text-secondary text-sm">Active Agents</p>
				<p class="text-2xl font-bold text-text-primary">{activeAgents}</p>
				<p class="text-xs text-text-secondary">
					{$agentsStore.agents.length} total agents
				</p>
			</div>
		</div>

		<!-- Sessions Card -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle glow-border card-hover">
			<div class="flex items-start justify-between mb-4">
				<div class="p-3 bg-neon-green/10 rounded-lg">
					<Terminal class="text-neon-green" size={24} />
				</div>
				{#if $sessionsStore.loading}
					<div class="animate-pulse w-2 h-2 bg-neon-green rounded-full"></div>
				{/if}
			</div>
			<div class="space-y-1">
				<p class="text-text-secondary text-sm">Active Sessions</p>
				<p class="text-2xl font-bold text-text-primary">{activeSessions}</p>
				<p class="text-xs text-text-secondary">
					{$sessionsStore.sessions.length} total sessions
				</p>
			</div>
		</div>
	</div>

	<!-- Recent Memories Preview -->
	<div class="bg-card-bg rounded-xl border border-border-subtle overflow-hidden">
		<div class="p-6 border-b border-border-subtle flex items-center justify-between">
			<div class="flex items-center gap-3">
				<Brain class="text-neon-cyan" size={20} />
				<h2 class="text-lg font-semibold text-text-primary">Recent Memories</h2>
			</div>
			<a href="/memory" class="text-neon-cyan hover:text-neon-cyan/80 text-sm font-medium transition-colors">
				View All →
			</a>
		</div>
		<div class="divide-y divide-border-subtle">
			{#if $memoryStore.loading}
				<div class="p-6 text-center text-text-secondary">
					<div class="animate-spin inline-block w-6 h-6 border-2 border-neon-cyan border-t-transparent rounded-full mb-2"></div>
					<p>Loading memories...</p>
				</div>
			{:else if $memoryStore.memories.length === 0}
				<div class="p-6 text-center text-text-secondary">
					<p>No memories yet. Start chatting with OpenAur!</p>
				</div>
			{:else}
				{#each $memoryStore.memories.slice(0, 5) as memory (memory.id)}
					<div class="p-4 hover:bg-card-hover transition-colors">
						<div class="flex items-start gap-3">
							<span class="px-2 py-1 text-xs font-medium bg-neon-cyan/10 text-neon-cyan rounded">
								{memory.memory_type}
							</span>
							<div class="flex-1 min-w-0">
								<p class="text-text-primary truncate">{memory.content}</p>
								<div class="flex items-center gap-2 mt-1">
									{#each memory.tags.slice(0, 3) as tag}
										<span class="text-xs text-text-secondary">#{tag}</span>
									{/each}
								</div>
							</div>
							<span class="text-xs text-text-secondary whitespace-nowrap">
								{new Date(memory.created_at).toLocaleDateString()}
							</span>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>

	<!-- System Info -->
	<div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-4">
				<Activity class="text-neon-cyan" size={20} />
				<h3 class="font-semibold text-text-primary">System Status</h3>
			</div>
			<div class="space-y-3">
				<div class="flex items-center justify-between">
					<span class="text-text-secondary">API</span>
					<span class="flex items-center gap-2 text-neon-green">
						<span class="status-dot active"></span>
						Operational
					</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-text-secondary">Analysis Engine</span>
					<span class="flex items-center gap-2 text-neon-green">
						<span class="status-dot active"></span>
						Operational
					</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-text-secondary">Two-Stage Processing</span>
					<span class="flex items-center gap-2 text-neon-green">
						<span class="status-dot active"></span>
						Operational
					</span>
				</div>
			</div>
		</div>

		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-4">
				<Zap class="text-neon-yellow" size={20} />
				<h3 class="font-semibold text-text-primary">Quick Actions</h3>
			</div>
			<div class="space-y-2">
				<a 
					href="/agents" 
					class="block p-3 rounded-lg bg-card-hover hover:bg-neon-cyan/5 border border-border-subtle hover:border-neon-cyan/30 transition-all"
				>
					<div class="flex items-center gap-3">
						<Bot size={18} class="text-neon-cyan" />
						<span class="text-text-primary">Spawn New Agent</span>
					</div>
				</a>
				<a 
					href="/memory" 
					class="block p-3 rounded-lg bg-card-hover hover:bg-neon-cyan/5 border border-border-subtle hover:border-neon-cyan/30 transition-all"
				>
					<div class="flex items-center gap-3">
						<Brain size={18} class="text-neon-purple" />
						<span class="text-text-primary">Browse Memories</span>
					</div>
				</a>
				<a 
					href="/sessions" 
					class="block p-3 rounded-lg bg-card-hover hover:bg-neon-cyan/5 border border-border-subtle hover:border-neon-cyan/30 transition-all"
				>
					<div class="flex items-center gap-3">
						<Terminal size={18} class="text-neon-green" />
						<span class="text-text-primary">View Sessions</span>
					</div>
				</a>
			</div>
		</div>
	</div>
</div>
