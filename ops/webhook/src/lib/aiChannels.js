/** Identify explicit AI sources; ordinary Google/Bing search stays unclassified. */
export function aiChannelOf(value) {
  var source = String(value || '').trim().toLowerCase();
  var aliases = {
    gpt: 'chatgpt', chatgpt: 'chatgpt', openai: 'chatgpt',
    claude: 'claude', anthropic: 'claude',
    perplexity: 'perplexity', gemini: 'gemini', copilot: 'copilot'
  };
  if (Object.prototype.hasOwnProperty.call(aliases, source)) return aliases[source];
  var host;
  try {
    host = new URL(source.indexOf('://') >= 0 ? source : 'https://' + source).hostname.replace(/\.$/, '');
  } catch (_) { return ''; }
  var domains = {
    'chatgpt.com': 'chatgpt', 'chat.openai.com': 'chatgpt',
    'claude.ai': 'claude', 'claude.com': 'claude',
    'perplexity.ai': 'perplexity', 'gemini.google.com': 'gemini',
    'copilot.microsoft.com': 'copilot', 'copilot.com': 'copilot'
  };
  for (var domain in domains) {
    if (host === domain || host.endsWith('.' + domain)) return domains[domain];
  }
  return '';
}
