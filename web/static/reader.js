function articleReader() {
    return {
        url: new URLSearchParams(window.location.search).get('url') || '',
        metadata: '',
        summary: '',
        fullText: '',
        error: '',
        isLoading: false,
        activeTab: 'summary',
        theme: localStorage.getItem('theme') || 'light-mode',
        hasResults: false,
        showToast: false,
        toastMessage: '',

        init() {
            this.$watch('theme', value => {
                localStorage.setItem('theme', value);
                document.body.className = value;
            });
            
            document.body.className = this.theme;
            
            if (this.url) {
                this.analyzeArticle();
            } else {
                window.location.href = '/';
            }
        },

        analyzeArticle() {
            this.isLoading = true;
            this.error = '';
            
            fetch(`/api/analyze?url=${encodeURIComponent(this.url)}`)
                .then(async response => {
                    const data = await response.json();
                    if (!response.ok) {
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
            const og = data.og_metadata;
            const title = og.title || 'No title available';
            const description = og.description || 'No description available';
            const image = og.image || '';
            const siteName = og.site_name || '';

            // Update meta tags
            this.updateMetaTags({
                title: this.escapeHtml(title),
                description: this.escapeHtml(description),
                image: encodeURI(image),
                url: this.url,
                siteName: this.escapeHtml(siteName)
            });

            // Update page title
            document.title = `${this.escapeHtml(title)} - Smmryzr`;

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

        updateMetaTags({ title, description, image, url, siteName }) {
            const tags = {
                'og:title': title,
                'og:description': description,
                'og:image': image,
                'og:url': url,
                'og:site_name': siteName
            };

            Object.entries(tags).forEach(([property, content]) => {
                const meta = document.querySelector(`meta[property="${property}"]`);
                if (meta) {
                    meta.setAttribute('content', content);
                } else {
                    const newMeta = document.createElement('meta');
                    newMeta.setAttribute('property', property);
                    newMeta.setAttribute('content', content);
                    document.head.appendChild(newMeta);
                }
            });
        },

        escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        },

        async shareArticle() {
            try {
                const currentUrl = new URL(window.location.href);
                const articleUrl = currentUrl.searchParams.get('url');
                if (!articleUrl) return;
                
                const previewUrl = `${window.location.origin}/preview/${encodeURIComponent(articleUrl)}`;
                
                // Check if device is mobile
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                
                if (isMobile && navigator.share) {
                    await navigator.share({
                        title: document.title,
                        text: 'Read this article on Smmryzr!',
                        url: previewUrl
                    });
                } else {
                    await navigator.clipboard.writeText(previewUrl);
                    this.showToast = true;
                    this.toastMessage = 'Share link copied to clipboard!';

                    // Hide toast after 3 seconds
                    setTimeout(() => {
                        this.showToast = false;
                    }, 3000);
                }
            } catch (err) {
                console.error('Error sharing:', err);
                this.showToast = true;
                this.toastMessage = 'Error sharing. Please try again.';

                // Hide toast after 3 seconds
                setTimeout(() => {
                    this.showToast = false;
                }, 3000);
            }
        }
    };
}