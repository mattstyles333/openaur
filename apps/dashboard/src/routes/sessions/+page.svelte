<script lang="ts">
	import { sessionsStore } from '$lib/stores';
	import { Terminal, Play, Square, Clock, Activity } from 'lucide-svelte';

	function getStatusColor(status: string): string {
		return status === 'active' ? 'text-neon-green' : 
			   status === 'completed' ? 'text-neon-cyan' : 
			   'text-text-secondary';
	}

	function formatDate(dateStr: string): string {
		if (!dateStr) return 'Unknown';
		try {
			const date = new Date(dateStr);
			if (isNaN(date.getTime())) return 'Unknown';
			return date.toLocaleString();
		} catch {
			return 'Unknown';
		}
	}

	// Reactive stats
	const activeCount = $derived($sessionsStore.sessions.filter((s: { status: string }) => s.status === 'active').length);
	const completedCount = $derived($sessionsStore.sessions.filter((s: { status: string }) => s.status === 'completed').length);
</script>

<svelte:head>
	<title>Session Manager | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<header class="mb-8">
		<div class="flex items-center gap-3 mb-2">
			<Terminal class="text-neon-green" size={28} />
			<h1 class="text-3xl font-bold text-text-primary">Session Manager</h1>
		</div>
		<p class="text-text-secondary">Active tmux sessions and command execution</p>
	</header>

	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Total Sessions</p>
			<p class="text-2xl font-bold text-text-primary">{$sessionsStore.sessions.length}</p>
		</div>
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Active</p>
			<p class="text-2xl font-bold text-neon-green">{activeCount}</p>
		</div>
		<div class="bg-card-bg rounded-lg p-4 border border-border-subtle">
			<p class="text-text-secondary text-sm mb-1">Completed</p>
			<p class="text-2xl font-bold text-neon-cyan">{completedCount}</p>
		</div>
	</div>

	<!-- Sessions Table -->
	<div class="bg-card-bg rounded-xl border border-border-subtle overflow-hidden">
		{#if $sessionsStore.loading}
			<div class="p-12 text-center">
				<div class="animate-spin inline-block w-8 h-8 border-2 border-neon-green border-t-transparent rounded-full mb-4"></div>
				<p class="text-text-secondary">Loading sessions...</p>
			</div>
		{:else if $sessionsStore.sessions.length === 0}
			<div class="p-12 text-center">
				<Terminal size={48} class="text-text-secondary mx-auto mb-4" />
				<p class="text-text-secondary text-lg">No active sessions</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead class="bg-card-hover border-b border-border-subtle">
						<tr>
							<th class="text-left p-4 text-text-secondary font-medium">Session</th>
							<th class="text-left p-4 text-text-secondary font-medium">Status</th>
							<th class="text-left p-4 text-text-secondary font-medium">Created</th>
							<th class="text-left p-4 text-text-secondary font-medium">PID</th>
							<th class="text-left p-4 text-text-secondary font-medium">Actions</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-border-subtle">
						{#each $sessionsStore.sessions as session (session.id)}
							<tr class="hover:bg-card-hover transition-colors">
								<td class="p-4">
									<div class="flex items-center gap-3">
										<Terminal size={18} class="text-neon-green" />
										<span class="text-text-primary mono">{session.name || session.id}</span>
									</div>
								</td>
								<td class="p-4">
									<span class="flex items-center gap-2 {getStatusColor(session.status)}">
										<Activity size={12} class={session.status === 'active' ? 'animate-pulse' : ''} />
										{session.status}
									</span>
								</td>
								<td class="p-4 text-text-secondary">
									{formatDate(session.created_at)}
								</td>
								<td class="p-4 text-text-secondary mono">
									{session.pid || '-'}
								</td>
								<td class="p-4">
									<div class="flex items-center gap-2">
										{#if session.status === 'active'}
											<button class="p-2 rounded-lg bg-neon-red/10 text-neon-red hover:bg-neon-red/20 transition-colors">
												<Square size={16} />
											</button>
										{/if}
										<button class="p-2 rounded-lg bg-neon-cyan/10 text-neon-cyan hover:bg-neon-cyan/20 transition-colors">
											<Terminal size={16} />
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
