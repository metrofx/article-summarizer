function articleAnalyzer() {
    return {
        url: new URLSearchParams(window.location.search).get('url') || '',
        metadata: '',
        summary: '',
        fullText: '',
        error: '',
        isLoading: false,
        activeTab: 'summary',
        theme: localStorage.getItem('theme') || 'light-mode',
        advancedOpen: false,
        permalink: '',
        hasResults: false,
        latestArticles: [],

        init() {
            // Watch for theme changes and save to localStorage
            this.$watch('theme', value => {
                localStorage.setItem('theme', value);
                document.body.className = value;
            });
            
            // Set initial theme
            document.body.className = this.theme;
            
            // Auto-analyze if URL is in query params
            if (this.url) {
                this.analyzeArticle();
            }

            // Load latest articles if no URL
            if (!this.url) {
                this.loadLatestArticles();
            }
        },

        analyzeArticle() {
            if (!this.url) return;
            
            this.isLoading = true;
            this.error = '';
            
            fetch(`/api/analyze?url=${encodeURIComponent(this.url)}`)
                .then(async response => {
                    const data = await response.json();
                    if (!response.ok) {
                        // Enhanced error logging
                        console.error('API Error:', {
                            status: response.status,
                            statusText: response.statusText,
                            data: data
                        });
                        throw new Error(data.detail || `HTTP error! Status: ${response.status}`);
                    }
                    return data;
                })
                .then(data => {
                    this.processData(data);
                    this.hasResults = true;
                })
                .catch(error => {
                    console.error('Request failed:', error);
                    this.error = `Error: ${error.message}`;
                    this.metadata = '';
                    this.summary = '';
                    this.fullText = '';
                    this.hasResults = false;
                })
                .finally(() => {
                    this.isLoading = false;
                });
        },

        processData(data) {
            console.group('Processing Article Data');
            
            // Extract metadata for display
            const og = data.og_metadata;
            const title = og.title || 'No title available';
            const description = og.description || 'No description available';
            const image = og.image || '';
            const siteName = og.site_name || '';

            console.log('Extracted OG Data:', { title, description, image, siteName });

            // Update permalink first
            this.updatePermalink();
            console.log('Updated Permalink:', this.permalink);

            // Enhanced updateMetaTag with logging
            const updateMetaTag = (property, content) => {
                console.log(`Updating ${property}:`, content);
                const meta = document.querySelector(`meta[property="${property}"]`);
                if (meta) {
                    const oldContent = meta.getAttribute('content');
                    meta.setAttribute('content', content);
                    console.log(`- Updated existing tag. Old: "${oldContent}" → New: "${content}"`);
                } else {
                    const newMeta = document.createElement('meta');
                    newMeta.setAttribute('property', property);
                    newMeta.setAttribute('content', content);
                    document.head.appendChild(newMeta);
                    console.log(`- Created new meta tag with content: "${content}"`);
                }
                
                // Verify update
                const verifyMeta = document.querySelector(`meta[property="${property}"]`);
                console.log(`- Verification - Current content: "${verifyMeta?.getAttribute('content')}"`);
            };

            // Update each meta tag
            updateMetaTag('og:title', this.escapeHtml(title));
            updateMetaTag('og:description', this.escapeHtml(description));
            updateMetaTag('og:image', encodeURI(image));
            updateMetaTag('og:url', this.permalink);
            updateMetaTag('og:site_name', this.escapeHtml(siteName));

            // Verify all meta tags after updates
            console.log('Final Meta Tags State:');
            document.querySelectorAll('meta[property^="og:"]').forEach(meta => {
                console.log(`${meta.getAttribute('property')}: "${meta.getAttribute('content')}"`);
            });

            // Update page title
            document.title = `Smmryzr - ${this.escapeHtml(title)}`;
            console.log('Updated page title:', document.title);

            console.groupEnd();

            // Create metadata card HTML
            this.metadata = `
                <div class="metadata-card">
                    <div class="metadata-content">
                        <div class="metadata-text">
                            <p class="site-name">${this.escapeHtml(siteName)}</p>
                            <h3>${this.escapeHtml(title)}</h3>
                            <p class="description">${this.escapeHtml(description)}</p>
                        </div>
                        <div class="metadata-footer">
                            ${image ? `<img src="${image}" alt="Article image">` : ''}
                        </div>
                    </div>
                </div>
            `;

            // Parse markdown and set content
            this.summary = marked.parse(data.content.summary || 'No summary available');
            this.fullText = marked.parse(data.content.full_text || 'No content available');
        },

        updatePermalink() {
            if (this.url) {
                const baseUrl = window.location.origin + window.location.pathname;
                this.permalink = `${baseUrl}?url=${encodeURIComponent(this.url)}`;
            } else {
                this.permalink = '';
            }
        },

        escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")  // Fixed regex here
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        },

        loadLatestArticles() {
            fetch('/api/latest')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    this.latestArticles = data.articles.map(article => {
                        const og = article.metadata;
                        return {
                            url: article.url,
                            title: og.title || 'No title available',
                            description: og.description || 'No description available',
                            image: og.image || '',
                            siteName: og.site_name || ''
                        };
                    });
                })
                .catch(error => {
                    console.error('Error loading latest articles:', error);
                });
        }
    };
}