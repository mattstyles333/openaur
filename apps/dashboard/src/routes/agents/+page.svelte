<script lang="ts">
	import { agentsStore } from '$lib/stores';
	import { Bot, Play, Pause, Square, Terminal, Clock, Zap } from 'lucide-svelte';

	function getStatusColor(state: string): string {
		const colors: Record<string, string> = {
			'running': 'text-neon-green',
			'idle': 'text-neon-yellow',
			'paused': 'text-neon-yellow',
			'completed': 'text-neon-cyan',
			'error': 'text-neon-red'
		};
		return colors[state] || 'text-text-secondary';
	}

	function getStatusBg(state: string): string {
		const bgs: Record<string, string> = {
			'running': 'bg-neon-green/10',
			'idle': 'bg-neon-yellow/10',
			'paused': 'bg-neon-yellow/10',
			'completed': 'bg-neon-cyan/10',
			'error': 'bg-neon-red/10'
		};
		return bgs[state] || 'bg-card-hover';
	}

	// Reactive stats
	const runningCount = $derived($agentsStore.agents.filter((a: { state: string }) => a.state === 'running').length);
	const idleCount = $derived($agentsStore.agents.filter((a: { state: string }) => a.state === 'idle').length);
	const errorCount = $derived($agentsStore.agents.filter((a: { state: string }) => a.state === 'error').length);
</script>

<svelte:head>
	<title>Agent Monitor | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<header class="mb-8">
		<div class="flex items-center gap-3 mb-2">
			<Bot class="text-neon-purple" size={28} />
			<h1 class="text-3xl font-bold text-text-primary">Agent Monitor</h1>
		</div>
		<p class="text-text-secondary">Monitor and manage active sub-agents</p>
	</header>

	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Total Agents</p>
			<p class="text-2xl font-bold text-text-primary">{$agentsStore.agents.length}</p>
		</div>
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Running</p>
			<p class="text-2xl font-bold text-neon-green">{runningCount}</p>
		</div>
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Idle</p>
			<p class="text-2xl font-bold text-neon-yellow">{idleCount}</p>
		</div>
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Errors</p>
			<p class="text-2xl font-bold text-neon-red">{errorCount}</p>
		</div>
	</div>

	<!-- Agents List -->
	<div class="bg-card-bg rounded-xl border border-border-subtle overflow-hidden">
		{#if $agentsStore.loading}
			<div class="p-12 text-center">
				<div class="animate-spin inline-block w-8 h-8 border-2 border-neon-purple border-t-transparent rounded-full mb-4"></div>
				<p class="text-text-secondary">Loading agents...</p>
			</div>
		{:else if $agentsStore.agents.length === 0}
			<div class="p-12 text-center">
				<Bot size={48} class="text-text-secondary mx-auto mb-4" />
				<p class="text-text-secondary text-lg">No agents running</p>
				<p class="text-text-secondary text-sm mt-2">Use the CLI to spawn agents: <code class="mono text-neon-cyan">openaur agents spawn</code></p>
			</div>
		{:else}
			<div class="divide-y divide-border-subtle">
				{#each $agentsStore.agents as agent (agent.id)}
					<div class="p-6 hover:bg-card-hover transition-colors">
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-4">
								<div class="p-3 bg-neon-purple/10 rounded-lg">
									<Bot class="text-neon-purple" size={24} />
								</div>
								<div>
									<h3 class="text-lg font-semibold text-text-primary">{agent.name}</h3>
									<p class="text-sm text-text-secondary mono">{agent.id}</p>
								</div>
							</div>
							<span class="px-3 py-1 text-sm font-medium rounded-full {getStatusBg(agent.state)} {getStatusColor(agent.state)}">
								{agent.state}
							</span>
						</div>

						<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
							<div class="flex items-center gap-2 text-sm text-text-secondary">
								<Zap size={16} class="text-neon-cyan" />
								<span>Iteration: {agent.iteration}/{agent.max_iterations}</span>
							</div>
							<div class="flex items-center gap-2 text-sm text-text-secondary">
								<Terminal size={16} class="text-neon-cyan" />
								<span>Queue: {agent.task_queue.length} tasks</span>
							</div>
							{#if agent.parent_id}
								<div class="flex items-center gap-2 text-sm text-text-secondary">
									<span>Parent: {agent.parent_id}</span>
								</div>
							{/if}
						</div>

						<!-- Progress bar -->
						<div class="mb-4">
							<div class="h-2 bg-deep-dark rounded-full overflow-hidden">
								<div 
									class="h-full bg-gradient-to-r from-neon-purple to-neon-cyan rounded-full transition-all duration-500"
									style="width: {(agent.iteration / agent.max_iterations) * 100}%"
								></div>
							</div>
						</div>

						<!-- Actions -->
						<div class="flex items-center gap-2">
							{#if agent.state === 'running'}
								<button class="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-yellow/10 text-neon-yellow hover:bg-neon-yellow/20 transition-colors">
									<Pause size={16} />
									<span>Pause</span>
								</button>
							{:else if agent.state === 'paused'}
								<button class="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-green/10 text-neon-green hover:bg-neon-green/20 transition-colors">
									<Play size={16} />
									<span>Resume</span>
								</button>
							{/if}
							<button class="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-red/10 text-neon-red hover:bg-neon-red/20 transition-colors">
								<Square size={16} />
								<span>Kill</span>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
