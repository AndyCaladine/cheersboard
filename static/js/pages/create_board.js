// CheersBoard — create_board.js
// Handles live sidebar updates on the Create Board form.
// Updates the summary panel as the user types and makes selections.

(function () {
    'use strict';

    // ── Tier data ─────────────────────────────────────────────
    const TIER_DATA = {
        free: {
            label:    'Free',
            price:    '£0',
            note:     'Your board is free. Share it straight away.',
            features: [
                'Up to 10 messages',
                '1 theme',
                'Shareable link',
                'Basic board view',
            ],
        },
        lite: {
            label:    'Lite',
            price:    '£4.99',
            note:     'One-off payment. No subscription.',
            features: [
                'Up to 30 messages',
                'More themes',
                'Shareable link & QR code',
                'PDF export',
            ],
        },
        premium: {
            label:    'Premium',
            price:    '£9.99',
            note:     'One-off payment. No subscription.',
            features: [
                'Unlimited messages',
                'All premium themes',
                'Shareable link & QR code',
                'PDF export',
                'Message moderation',
            ],
        },
        event: {
            label:    'Event',
            price:    '£19.99',
            note:     'One-off payment. No subscription.',
            features: [
                'Everything in Premium',
                'Live slideshow mode',
                'OBS browser source',
                'Embed on any website',
            ],
        },
    };

    // ── Element refs ──────────────────────────────────────────
    const form            = document.getElementById('createBoardForm');
    const summaryName     = document.getElementById('summaryName');
    const summaryRecipient= document.getElementById('summaryRecipient');
    const summaryOccasion = document.getElementById('summaryOccasion');
    const summaryTheme    = document.getElementById('summaryTheme');
    const summaryLayout   = document.getElementById('summaryLayout');
    const summaryTierName = document.getElementById('summaryTierName');
    const summaryPrice    = document.getElementById('summaryPrice');
    const summaryNote     = document.getElementById('summaryNote');
    const summaryFeatures = document.getElementById('summaryFeatures');
    const messageTextarea = document.getElementById('creator_message');
    const messageCount    = document.getElementById('messageCount');

    if (!form) return;

    // ── Character counter ─────────────────────────────────────
    if (messageTextarea && messageCount) {
        messageTextarea.addEventListener('input', function () {
            messageCount.textContent = this.value.length;
        });
        // Set on load in case of server-side repopulation
        messageCount.textContent = messageTextarea.value.length;
    }

    // ── Sidebar update ────────────────────────────────────────
    function updateSummary() {
        // Board name
        const nameVal = (document.getElementById('board_name').value || '').trim();
        summaryName.textContent = nameVal || '—';

        // Recipient
        const recipientVal = (document.getElementById('recipient_name').value || '').trim();
        summaryRecipient.textContent = recipientVal || '—';

        // Occasion
        const checkedOccasion = form.querySelector('input[name="occasion_id"]:checked');
        if (checkedOccasion) {
            const pill = checkedOccasion.closest('.cb-occasion-pill');
            summaryOccasion.textContent = pill ? pill.textContent.trim() : '—';
        } else {
            summaryOccasion.textContent = '—';
        }

        // Theme + tier
        const checkedTheme = form.querySelector('input[name="theme_id"]:checked');
        if (checkedTheme) {
            const card   = checkedTheme.closest('.cb-theme-card');
            const tier   = card ? card.dataset.tier : null;
            const name   = card ? card.querySelector('.cb-theme-card__name').textContent.trim() : '—';
            const layout = card ? card.querySelector('.cb-theme-card__layout').textContent.trim() : '—';

            summaryTheme.textContent  = name;
            summaryLayout.textContent = layout;

            if (tier && TIER_DATA[tier]) {
                const t = TIER_DATA[tier];
                summaryTierName.textContent = t.label;
                summaryPrice.textContent    = t.price;
                summaryNote.textContent     = t.note;
                renderFeatures(t.features);
            }
        } else {
            summaryTheme.textContent  = '—';
            summaryLayout.textContent = '—';
            summaryTierName.textContent = 'Free';
            summaryPrice.textContent    = '£0';
            summaryNote.textContent     = 'Choose a theme to see your price.';
            summaryFeatures.innerHTML   = '';
        }

        // Occasion pill selected state (CSS :has fallback for older browsers)
        form.querySelectorAll('.cb-occasion-pill').forEach(function (pill) {
            const radio = pill.querySelector('input[type="radio"]');
            pill.classList.toggle('cb-occasion-pill--selected', radio && radio.checked);
        });

        // Theme card selected state
        form.querySelectorAll('.cb-theme-card').forEach(function (card) {
            const radio = card.querySelector('input[type="radio"]');
            card.classList.toggle('cb-theme-card--selected', radio && radio.checked);
        });
    }

    function renderFeatures(features) {
        summaryFeatures.innerHTML = features.map(function (f) {
            return '<div class="cb-summary__feature">' + f + '</div>';
        }).join('');
    }

    // ── Event listeners ───────────────────────────────────────
    form.addEventListener('input', updateSummary);
    form.addEventListener('change', updateSummary);

    // ── Init on load ──────────────────────────────────────────
    updateSummary();

}());