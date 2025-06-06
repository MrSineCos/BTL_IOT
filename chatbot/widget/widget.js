self.onInit = function() {
    const ctx = self.ctx;
    const ds = ctx.datasources || [];

    // Tìm data source cho Attributes (Server/Shared/Client)
    // Trong TB v3+, attribute datasource thường có type = 'entityAttribute'
    const attrDs = ds.find(d =>
        d.type === 'entityAttribute' ||
        (d.type === 'attributes' && d
            .datasourceType === 'SERVER'
            ) // tuỳ version
    );

    if (attrDs && attrDs.dataKeys && attrDs.dataKeys
        .length) {
        // keyName hoặc name tuỳ TB version
        this.requestAttrKey = attrDs.dataKeys[0]
            .keyName || attrDs.dataKeys[0].name;
        // Xác định scope dựa vào nguồn bạn cấu hình (SERVER/SHARED/CLIENT)
        switch (attrDs.datasourceType) {
            case 'SHARED':
                this.requestAttrScope = 'SHARED_SCOPE';
                break;
            case 'CLIENT':
                this.requestAttrScope = 'CLIENT_SCOPE';
                break;
            default:
                this.requestAttrScope = 'SERVER_SCOPE';
        }
    } else {
        console.error(
            'Không tìm thấy Data Source Attribute, vui lòng kiểm tra lại trong Widget → Datasources'
            );
        // fallback nếu cần
        this.requestAttrKey = ctx.settings
            .requestAttrKey || 'lastQuestion';
        this.requestAttrScope = ctx.settings
            .requestAttrScope || 'SERVER_SCOPE';
    }

    // --- Phần DOM và logic chat như trước ---
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById(
        'sendButton');
    const messagesList = document.getElementById(
        'messagesList');
    const charCounter = document.getElementById(
        'charCounter');

    function formatTime(ts) {
        const d = new Date(ts);
        return d.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function scrollToBottom() {
        const c = document.getElementById(
            'messagesContainer');
        c.scrollTop = c.scrollHeight;
    }

    this.addMessage = function(text, isUser) {
        const w = document.createElement('div');
        w.classList.add('message', isUser ? 'user' :
            'bot');
        w.innerHTML = text.replace(/\n/g, '<br>');
        const t = document.createElement('div');
        t.classList.add('message-time');
        t.textContent = formatTime(Date.now());
        w.appendChild(t);
        messagesList.appendChild(w);
        scrollToBottom();
    };

    this.sendMessage = function() {
        const txt = input.value.trim();
        if (!txt) return;
        this.addMessage(txt, true);
        const attrs = {};
        attrs[this.requestAttrKey] = txt;
        ctx.updateEntityAttributes(this
            .requestAttrScope, attrs, () => {
                console.log(
                    'Attribute updated:',
                    this.requestAttrKey, txt
                    );
            });
        input.value = '';
        charCounter.textContent = '0/500';
    };

    input.addEventListener('input', () => {
        charCounter.textContent =
            `${input.value.length}/500`;
    });
    sendBtn.addEventListener('click', this.sendMessage
        .bind(this));
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    });
};

// self.onInit = function() {
// }

self.onDataUpdated = function() {
    //  self.ctx.$scope.multipleInputWidget.onDataUpdated();
}
