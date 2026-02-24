<script lang="ts">
	import { Settings, Key, Cpu, Save, Check, AlertCircle, Sparkles, Heart, Zap } from 'lucide-svelte';
	import { api } from '$lib/api';

	let apiKey = $state('');
	let hasKey = $state(false);
	let saveStatus = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	let modelSaveStatus = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	
	// Chat Model (Main AI)
	let selectedModel = $state('openrouter/auto');
	let customModel = $state('');
	let useCustomModel = $state(false);
	
	// Heart Model (Empathy/Analysis)
	let selectedHeartModel = $state('openai/gpt-oss-20b:nitro');
	let customHeartModel = $state('');
	let useCustomHeartModel = $state(false);
	
	// Instant Preview - Get fast response while waiting for quality model
	let instantPreview = $state(false);
	
	// Load saved configuration on mount
	let configLoaded = $state(false);

	const chatModels = [
		{ id: 'openrouter/auto', name: 'Auto (Default)', desc: 'Best model for the task' },
		{ id: 'moonshotai/kimi-k2.5', name: 'Kimi K2.5', desc: 'Moonshot AI' },
		{ id: 'minimax/minimax-m2.5', name: 'MiniMax M2.5', desc: 'MiniMax' },
		{ id: 'deepseek/deepseek-v3.2', name: 'DeepSeek V3.2', desc: 'DeepSeek' },
		{ id: 'custom', name: 'Custom', desc: 'Enter any OpenRouter model' },
	];

	const heartModels = [
		{ id: 'openai/gpt-oss-20b:nitro', name: 'GPT-OSS 20B Nitro', desc: 'Fast OSS model (default)' },
		{ id: 'meta-llama/llama-3.1-8b-instruct:nitro', name: 'Llama 3.1 8B Nitro', desc: 'Meta - Fast & efficient' },
		{ id: 'meta-llama/llama-4-scout:nitro', name: 'Llama 4 Scout Nitro', desc: 'Meta - Latest Llama' },
		{ id: 'custom', name: 'Custom', desc: 'Enter any OpenRouter model' },
	];

	$effect(() => {
		// Only run once on mount
		if (!configLoaded) {
			loadConfig();
		}
	});

	async function loadConfig() {
		try {
			// Load from new settings API
			const settingsRes = await fetch(`${api.baseUrl}/settings/`);
			if (settingsRes.ok) {
				const settings = await settingsRes.json();
				
				// Load chat model
				if (settings.chat_model) {
					if (chatModels.find(m => m.id === settings.chat_model)) {
						selectedModel = settings.chat_model;
					} else {
						selectedModel = 'custom';
						customModel = settings.chat_model;
						useCustomModel = true;
					}
				}
				
				// Load heart model
				if (settings.heart_model) {
					if (heartModels.find(m => m.id === settings.heart_model)) {
						selectedHeartModel = settings.heart_model;
					} else {
						selectedHeartModel = 'custom';
						customHeartModel = settings.heart_model;
						useCustomHeartModel = true;
					}
				}
				
				// Load instant preview setting
				if (settings.instant_preview !== undefined) {
					instantPreview = settings.instant_preview;
				}
			}
			
			// Check API key status
			const res = await fetch(`${api.baseUrl}/api/config/status`);
			const data = await res.json();
			hasKey = data.has_api_key;
			
			configLoaded = true;
		} catch {
			hasKey = false;
			configLoaded = true;
		}
	}

	async function saveApiKey() {
		if (!apiKey || apiKey.length < 20) return;
		
		saveStatus = 'saving';
		try {
			const res = await fetch(`${api.baseUrl}/api/config/api-key`, {
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

	async function saveModels() {
		modelSaveStatus = 'saving';
		
		const chatModelId = useCustomModel && customModel ? customModel : selectedModel;
		const heartModelId = useCustomHeartModel && customHeartModel ? customHeartModel : selectedHeartModel;
		
		try {
			// Save to new settings API (batch update)
			const res = await fetch(`${api.baseUrl}/settings/batch`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					settings: {
						chat_model: chatModelId,
						heart_model: heartModelId,
						instant_preview: instantPreview
					}
				})
			});
			
			if (res.ok) {
				modelSaveStatus = 'saved';
				setTimeout(() => modelSaveStatus = 'idle', 3000);
			} else {
				modelSaveStatus = 'error';
			}
		} catch {
			modelSaveStatus = 'error';
		}
	}

	function handleModelChange(modelId: string) {
		selectedModel = modelId;
		useCustomModel = modelId === 'custom';
		if (!useCustomModel) {
			customModel = '';
		}
	}

	function handleHeartModelChange(modelId: string) {
		selectedHeartModel = modelId;
		useCustomHeartModel = modelId === 'custom';
		if (!useCustomHeartModel) {
			customHeartModel = '';
		}
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
		<p class="text-text-secondary">Manage API keys and AI models</p>
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

		<!-- Chat Model Selection -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-purple/10 rounded-lg">
					<Sparkles class="text-neon-purple" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">Chat Model</h2>
					<p class="text-sm text-text-secondary">Main AI for conversations</p>
				</div>
			</div>

			<div class="space-y-3">
				{#each chatModels as model}
					<button
						class="w-full p-4 rounded-lg border transition-all text-left {selectedModel === model.id ? 'border-neon-purple bg-neon-purple/10' : 'border-border-subtle hover:border-neon-purple/50'}"
						onclick={() => handleModelChange(model.id)}
					>
						<div class="flex items-center justify-between">
							<div>
								<p class="font-medium text-text-primary">{model.name}</p>
								<p class="text-sm text-text-secondary font-mono text-xs mt-0.5">{model.id}</p>
							</div>
							{#if selectedModel === model.id}
								<div class="w-4 h-4 rounded-full bg-neon-purple"></div>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			{#if useCustomModel}
				<div class="mt-4">
					<input
						type="text"
						bind:value={customModel}
						placeholder="Enter OpenRouter model ID..."
						class="w-full px-4 py-3 bg-deep-dark border border-border-subtle rounded-lg text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-neon-purple transition-colors"
					/>
				</div>
			{/if}
		</div>

		<!-- Heart Model Selection -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-red/10 rounded-lg">
					<Heart class="text-neon-red" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">Heart Model</h2>
					<p class="text-sm text-text-secondary">Empathy & analysis engine</p>
				</div>
			</div>

			<div class="space-y-3">
				{#each heartModels as model}
					<button
						class="w-full p-4 rounded-lg border transition-all text-left {selectedHeartModel === model.id ? 'border-neon-red bg-neon-red/10' : 'border-border-subtle hover:border-neon-red/50'}"
						onclick={() => handleHeartModelChange(model.id)}
					>
						<div class="flex items-center justify-between">
							<div>
								<p class="font-medium text-text-primary">{model.name}</p>
								<p class="text-sm text-text-secondary font-mono text-xs mt-0.5">{model.id}</p>
							</div>
							{#if selectedHeartModel === model.id}
								<div class="w-4 h-4 rounded-full bg-neon-red"></div>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			{#if useCustomHeartModel}
				<div class="mt-4">
					<input
						type="text"
						bind:value={customHeartModel}
						placeholder="Enter OpenRouter model ID..."
						class="w-full px-4 py-3 bg-deep-dark border border-border-subtle rounded-lg text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-neon-red transition-colors"
					/>
				</div>
			{/if}

			<div class="mt-6 p-4 bg-deep-dark rounded-lg">
				<p class="text-sm text-text-secondary">
					<strong class="text-text-primary">Note:</strong> The Heart model handles empathy, sentiment analysis, and system health checks. OSS models keep costs down for these frequent operations.
				</p>
			</div>
		</div>

		<!-- Instant Preview Feature -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-3 bg-neon-yellow/10 rounded-lg">
					<Zap class="text-neon-yellow" size={24} />
				</div>
				<div>
					<h2 class="text-xl font-semibold text-text-primary">Instant Preview</h2>
					<p class="text-sm text-text-secondary">Get fast responses while waiting</p>
				</div>
			</div>

			<div class="space-y-4">
				<div class="flex items-center justify-between p-4 rounded-lg border border-border-subtle">
					<div>
						<p class="font-medium text-text-primary">Enable Instant Preview</p>
						<p class="text-sm text-text-secondary">Show quick response from fast model immediately</p>
					</div>
					<button
						onclick={() => instantPreview = !instantPreview}
						class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors {instantPreview ? 'bg-neon-cyan' : 'bg-border-subtle'}"
					>
						<span
							class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform {instantPreview ? 'translate-x-6' : 'translate-x-1'}"
						/>
					</button>
				</div>

				{#if instantPreview}
					<div class="p-4 bg-neon-yellow/5 border border-neon-yellow/20 rounded-lg">
						<p class="text-sm text-text-secondary">
							<strong class="text-neon-yellow">How it works:</strong> When you send a message, the fast model (Heart) generates an immediate response shown in <span class="italic">italics</span>. The main chat model then provides the full response shortly after. Perfect for quick questions where you don't want to wait!
						</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- Save Models Button -->
		<div class="bg-card-bg rounded-xl p-6 border border-border-subtle lg:col-span-2">
			<button
				onclick={saveModels}
				disabled={modelSaveStatus === 'saving'}
				class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-neon-cyan text-deep-dark font-medium hover:bg-neon-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
			>
				{#if modelSaveStatus === 'saving'}
					<div class="animate-spin w-4 h-4 border-2 border-deep-dark border-t-transparent rounded-full"></div>
					<span>Saving...</span>
				{:else if modelSaveStatus === 'saved'}
					<Check size={18} />
					<span>Models Saved!</span>
				{:else}
					<Save size={18} />
					<span>Save Model Settings</span>
				{/if}
			</button>
		</div>
	</div>
</div>
