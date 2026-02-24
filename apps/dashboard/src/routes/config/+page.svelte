<script lang="ts">
	import { Settings, Key, Cpu, Save, Check, AlertCircle } from 'lucide-svelte';
	import { onMount } from 'svelte';

	let apiKey = $state('');
	let hasKey = $state(false);
	let saveStatus = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	let selectedModel = $state('openaura/default');
	let autoRefreshInterval = $state(5);

	const models = [
		{ id: 'openaura/default', name: 'OpenAura Default', desc: 'Balanced quality & speed' },
		{ id: 'openaura/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', desc: 'High quality, slower' },
		{ id: 'openaura/gpt-4o', name: 'GPT-4o', desc: 'Latest GPT-4 optimized' },
	];

	onMount(async () => {
		// Check if API key exists
		try {
			const res = await fetch('/api/config/status');
			const data = await res.json();
			hasKey = data.has_api_key;
		} catch {
			hasKey = false;
		}
	});

	async function saveApiKey() {
		if (!apiKey || apiKey.length < 20) return;
		
		saveStatus = 'saving';
		try {
			const res = await fetch('/api/config/api-key', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ api_key: apiKey })
			});
			
			if (res.ok) {
				saveStatus = 'saved';
				hasKey = true;
				apiKey = ''; // Clear input
				setTimeout(() => saveStatus = 'idle', 3000);
			} else {
				saveStatus = 'error';
			}
		} catch {
			saveStatus = 'error';
		}
	}

	function maskKey(key: string): string {
		if (key.length < 10) return key;
		return key.slice(0, 6) + '...' + key.slice(-4);
	}
</script>

<svelte:head>
	<title>Configuration | OpenAur Dashboard</title>
</svelte:head>

<div class="p-8">
	<header class="mb-8">
		<div class="flex items-center gap-3 mb-2">
			<Settings class="text-neon-cyan" size={28} />
			<h1 class="text-3xl font-bold text-text-primary">Configuration</h1>
		</div>
		<p class="text-text-secondary">Manage API keys, models, and system settings</p>
	</header>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<!-- API Key Configuration -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle glow-border">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-cyan/10 rounded-lg">
					<Key class="text-neon-cyan" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">OpenRouter API Key</h2>
					<p class="text-sm text-text-secondary">Required for AI features</p>
				</div>
			</div>

			{#if hasKey}
				<div class="mb-6 p-4 bg-neon-green/10 border border-neon-green/30 rounded-lg">
					<div class="flex items-center gap-2 text-neon-green">
						<Check size={18} />
						<span class="font-medium">API key configured</span>
					</div>
					<p class="text-sm text-text-secondary mt-1">
						Your API key is saved and active. You can update it below.
					</p>
				</div>
			{:else}
				<div class="mb-6 p-4 bg-neon-yellow/10 border border-neon-yellow/30 rounded-lg">
					<div class="flex items-center gap-2 text-neon-yellow">
						<AlertCircle size={18} />
						<span class="font-medium">API key required</span>
					</div>
					<p class="text-sm text-text-secondary mt-1">
						Get your API key from <a href="https://openrouter.ai/keys" target="_blank" class="text-neon-cyan hover:underline">openrouter.ai/keys</a>
					</p>
				</div>
			{/if}

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-text-secondary mb-2">
						API Key
					</label>
					<input
						type="password"
						bind:value={apiKey}
						placeholder="sk-or-v1-..."
						class="w-full px-4 py-3 bg-deep-dark border border-border-subtle rounded-lg text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-neon-cyan transition-colors"
					/>
					<p class="text-xs text-text-secondary mt-1">
						Your key should start with "sk-or-v1-"
					</p>
				</div>

				<button
					onclick={saveApiKey}
					disabled={!apiKey || apiKey.length < 20 || saveStatus === 'saving'}
					class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-neon-cyan text-deep-dark font-medium hover:bg-neon-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
				>
					{#if saveStatus === 'saving'}
						<div class="animate-spin w-4 h-4 border-2 border-deep-dark border-t-transparent rounded-full"></div>
						<span>Saving...</span>
					{:else if saveStatus === 'saved'}
						<Check size={18} />
						<span>Saved!</span>
					{:else}
						<Save size={18} />
						<span>Save API Key</span>
					{/if}
				</button>
			</div>
		</div>

		<!-- Model Selection -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-purple/10 rounded-lg">
					<Cpu class="text-neon-purple" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">AI Model</h2>
					<p class="text-sm text-text-secondary">Select your preferred model</p>
				</div>
			</div>

			<div class="space-y-3">
				{#each models as model}
					<button
						class="w-full p-4 rounded-lg border transition-all text-left {selectedModel === model.id ? 'border-neon-cyan bg-neon-cyan/10' : 'border-border-subtle hover:border-neon-cyan/50'}"
						onclick={() => selectedModel = model.id}
					>
						<div class="flex items-center justify-between">
							<div>
								<p class="font-medium text-text-primary">{model.name}</p>
								<p class="text-sm text-text-secondary">{model.desc}</p>
							</div>
							{#if selectedModel === model.id}
								<div class="w-4 h-4 rounded-full bg-neon-cyan"></div>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			<div class="mt-6 p-4 bg-deep-dark rounded-lg">
				<p class="text-sm text-text-secondary">
					<strong class="text-text-primary">Note:</strong> Model selection affects response quality and speed. 
					Changes take effect immediately for new conversations.
				</p>
			</div>
		</div>

		<!-- Dashboard Settings -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-green/10 rounded-lg">
					<Settings class="text-neon-green" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">Dashboard Settings</h2>
					<p class="text-sm text-text-secondary">Customize your experience</p>
				</div>
			</div>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-text-secondary mb-2">
						Auto-refresh Interval (seconds)
					</label>
					<div class="flex items-center gap-4">
						<input
							type="range"
							min="1"
							max="30"
							bind:value={autoRefreshInterval}
							class="flex-1 h-2 bg-deep-dark rounded-lg appearance-none cursor-pointer accent-neon-cyan"
						/>
						<span class="text-text-primary font-mono w-12 text-right">{autoRefreshInterval}s</span>
					</div>
				</div>

				<div class="p-4 bg-deep-dark rounded-lg">
					<p class="text-sm text-text-secondary">
						<strong class="text-text-primary">Memory Display:</strong> 
						System memories (pre-loaded context) are hidden from the dashboard. 
						Only user queries, assistant responses, and action learnings are shown.
					</p>
				</div>
			</div>
		</div>
	</div>
</div>
