<script lang="ts">
	import { heartStore } from '$lib/stores';
	import { Heart, Activity, Cpu, Zap, Clock } from 'lucide-svelte';

	const status = $derived($heartStore.status?.heart);
</script>

<svelte:head>
	<title>Heart Status | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<header class="mb-8">
		<div class="flex items-center gap-3 mb-2">
			<Heart class="text-neon-red heart-pulse" size={28} />
			<h1 class="text-3xl font-bold text-text-primary">Heart Status</h1>
		</div>
		<p class="text-text-secondary">System health and emotional state</p>
	</header>

	{#if $heartStore.loading}
		<div class="flex items-center justify-center p-12">
			<div class="animate-spin w-12 h-12 border-4 border-neon-red border-t-transparent rounded-full"></div>
		</div>
	{:else if $heartStore.error}
		<div class="bg-neon-red/10 border border-neon-red/30 rounded-xl p-8 text-center">
			<Heart size={48} class="text-neon-red mx-auto mb-4" />
			<p class="text-neon-red text-lg">{$heartStore.error}</p>
		</div>
	{:else if status}
		<!-- Main Heart Display -->
		<div class="bg-card-bg rounded-2xl p-8 border border-border-subtle mb-8 glow-border">
			<div class="flex flex-col md:flex-row items-center justify-between gap-8">
				<div class="text-center">
					<div class="relative inline-block mb-4">
						<div class="absolute inset-0 bg-neon-red/20 blur-3xl rounded-full animate-pulse"></div>
						<Heart size={80} class="text-neon-red relative z-10 heart-pulse" />
					</div>
					<p class="text-4xl font-bold gradient-text mb-2">{status.vitals.status}</p>
					<p class="text-text-secondary">{$heartStore.status.pulse}</p>
				</div>

				<div class="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
					<div class="bg-deep-dark rounded-lg p-4 border border-border-subtle">
						<p class="text-text-secondary text-sm mb-1">Status</p>
						<p class="text-xl font-bold text-neon-green">{status.physical.status}</p>
					</div>
					<div class="bg-deep-dark rounded-lg p-4 border border-border-subtle">
						<p class="text-text-secondary text-sm mb-1">Mood</p>
						<p class="text-xl font-bold text-neon-cyan">{status.emotional.mood}</p>
					</div>
					<div class="bg-deep-dark rounded-lg p-4 border border-border-subtle">
						<p class="text-text-secondary text-sm mb-1">Version</p>
						<p class="text-xl font-bold text-text-primary mono">{status.vitals.version}</p>
					</div>
					<div class="bg-deep-dark rounded-lg p-4 border border-border-subtle">
						<p class="text-text-secondary text-sm mb-1">Model</p>
						<p class="text-sm font-bold text-neon-purple truncate">{status.emotional.model}</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Physical Health -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
			<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
				<div class="flex items-center gap-3 mb-4">
					<Activity class="text-neon-green" size={20} />
					<h2 class="text-lg font-semibold text-text-primary">Physical Health</h2>
				</div>
				<div class="space-y-3">
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">Service</span>
						<span class="text-neon-green font-medium">{status.physical.service}</span>
					</div>
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">Analysis Engine</span>
						<span class="text-neon-green font-medium">{status.physical.analysis_engine}</span>
					</div>
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">Two-Stage Processing</span>
						<span class="text-neon-green font-medium">{status.physical.two_stage_processing}</span>
					</div>
				</div>
			</div>

			<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
				<div class="flex items-center gap-3 mb-4">
					<Cpu class="text-neon-cyan" size={20} />
					<h2 class="text-lg font-semibold text-text-primary">Emotional State</h2>
				</div>
				<div class="space-y-3">
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">State</span>
						<span class="text-neon-cyan font-medium">{status.emotional.state}</span>
					</div>
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">Awareness</span>
						<span class="text-neon-cyan font-medium">{status.emotional.awareness}</span>
					</div>
					<div class="flex items-center justify-between p-3 rounded-lg bg-deep-dark">
						<span class="text-text-secondary">Processing</span>
						<span class="text-neon-purple font-medium">{status.emotional.model}</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Timestamp -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3">
				<Clock class="text-neon-yellow" size={20} />
				<div>
					<p class="text-text-secondary text-sm">Last Updated</p>
					<p class="text-text-primary font-medium">{new Date(status.vitals.timestamp).toLocaleString()}</p>
				</div>
			</div>
		</div>
	{/if}
</div>
