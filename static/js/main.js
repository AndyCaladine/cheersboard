// CheersBoard — main.js
// Shared JS behaviour across the app.
// Flash messages close on click (handled inline in base.html).

// ============================================================
// Hero Fireworks
// Runs only on pages that include #heroFireworksCanvas.
// Renders looping firework bursts on a canvas layered inside
// the hero section, using the brand colour palette.
// ============================================================

(function () {
    'use strict';

    const canvas = document.getElementById('heroFireworksCanvas');
    if (!canvas) return; // Not on the home page — bail out.

    const ctx = canvas.getContext('2d');

    // Size the canvas to the hero section's actual rendered dimensions.
    // offsetWidth/Height read 0 before layout is painted, so we read
    // from the parent .hero element and fall back to the viewport.
    function resize() {
        const hero    = canvas.closest('.hero') || document.body;
        canvas.width  = hero.offsetWidth  || window.innerWidth;
        canvas.height = hero.offsetHeight || window.innerHeight;
    }

    // Run once the layout has painted, then on every resize.
    resize();
    window.addEventListener('resize', resize);

    // ── Brand palette ──────────────────────────────────────────
    const COLOURS = [
        '#F5C518', // yellow
        '#F26B6B', // coral
        '#2ABFBF', // teal
        '#8B5CF6', // purple
        '#5BC95B', // green
        '#F472B6', // pink
        '#FFFFFF', // white (sparkle ring)
        '#FFE066', // warm yellow variant
        '#7DD3FC', // sky blue
        '#FB923C', // orange
    ];

    function randColour() {
        return COLOURS[Math.floor(Math.random() * COLOURS.length)];
    }

    // ── Firework particle ───────────────────────────────────────
    function FireworkParticle(x, y, colour) {
        const angle  = Math.random() * Math.PI * 2;
        const speed  = 2 + Math.random() * 6;
        this.x       = x;
        this.y       = y;
        this.vx      = Math.cos(angle) * speed;
        this.vy      = Math.sin(angle) * speed;
        this.colour  = colour;
        this.life    = 1;
        this.decay   = 0.012 + Math.random() * 0.018;
        this.size    = 2.5 + Math.random() * 3;
        this.gravity = 0.1;
        this.trail   = [];
    }

    FireworkParticle.prototype.update = function () {
        this.trail.push({ x: this.x, y: this.y });
        if (this.trail.length > 6) this.trail.shift();
        this.vy  += this.gravity;
        this.vx  *= 0.98;
        this.x   += this.vx;
        this.y   += this.vy;
        this.life -= this.decay;
    };

    FireworkParticle.prototype.draw = function () {
        for (let i = 0; i < this.trail.length; i++) {
            const t     = this.trail[i];
            const alpha = (i / this.trail.length) * this.life * 0.35;
            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.fillStyle   = this.colour;
            ctx.beginPath();
            ctx.arc(t.x, t.y, this.size * 0.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle   = this.colour;
        ctx.shadowColor = this.colour;
        ctx.shadowBlur  = 8;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    };

    FireworkParticle.prototype.isDead = function () {
        return this.life <= 0;
    };

    // ── Firework (rocket + burst) ───────────────────────────────
    function Firework() {
        this.launch();
    }

    Firework.prototype.launch = function () {
        this.x         = canvas.width * 0.1 + Math.random() * canvas.width * 0.8;
        this.y         = canvas.height;
        this.targetY   = canvas.height * 0.08 + Math.random() * canvas.height * 0.5;
        this.vy        = -14 - Math.random() * 8;
        this.colour    = randColour();
        this.exploded  = false;
        this.particles = [];
        this.trail     = [];
    };

    Firework.prototype.update = function () {
        if (!this.exploded) {
            this.trail.push({ x: this.x, y: this.y });
            if (this.trail.length > 10) this.trail.shift();
            this.vy *= 0.98;
            this.y  += this.vy;
            if (this.y <= this.targetY || this.vy >= -1) {
                this._explode();
            }
        } else {
            for (let i = this.particles.length - 1; i >= 0; i--) {
                this.particles[i].update();
                if (this.particles[i].isDead()) this.particles.splice(i, 1);
            }
        }
    };

    Firework.prototype._explode = function () {
        this.exploded = true;
        const count        = 80 + Math.floor(Math.random() * 60);
        const cx           = this.x;
        const cy           = this.y;
        const burstColours = [this.colour];
        if (Math.random() < 0.5) burstColours.push(randColour());

        for (let i = 0; i < count; i++) {
            const c = burstColours[Math.floor(Math.random() * burstColours.length)];
            this.particles.push(new FireworkParticle(cx, cy, c));
        }
        // Tight sparkle ring
        for (let j = 0; j < 24; j++) {
            const angle = (j / 24) * Math.PI * 2;
            const p     = new FireworkParticle(cx, cy, '#FFFFFF');
            p.vx        = Math.cos(angle) * 9;
            p.vy        = Math.sin(angle) * 9;
            p.size      = 1.5;
            p.decay     = 0.03;
            this.particles.push(p);
        }
    };

    Firework.prototype._drawRocket = function () {
        if (this.exploded) return;
        for (let i = 0; i < this.trail.length; i++) {
            const t     = this.trail[i];
            const alpha = (i / this.trail.length) * 0.6;
            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.fillStyle   = this.colour;
            ctx.shadowColor = this.colour;
            ctx.shadowBlur  = 6;
            ctx.beginPath();
            ctx.arc(t.x, t.y, 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
        ctx.save();
        ctx.globalAlpha = 1;
        ctx.fillStyle   = '#FFFFFF';
        ctx.shadowColor = this.colour;
        ctx.shadowBlur  = 14;
        ctx.beginPath();
        ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    };

    Firework.prototype.draw = function () {
        this._drawRocket();
        for (let i = 0; i < this.particles.length; i++) {
            this.particles[i].draw();
        }
    };

    Firework.prototype.isDone = function () {
        return this.exploded && this.particles.length === 0;
    };

    // ── Loop ───────────────────────────────────────────────────
    let fireworks         = [];
    let lastLaunchTime    = 0;
    const LAUNCH_INTERVAL = 850;

    // Stagger initial bursts so the hero looks alive immediately.
    setTimeout(() => fireworks.push(new Firework()), 300);
    setTimeout(() => fireworks.push(new Firework()), 750);
    setTimeout(() => fireworks.push(new Firework()), 1300);

    function loop(ts) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (ts - lastLaunchTime > LAUNCH_INTERVAL) {
            fireworks.push(new Firework());
            if (Math.random() < 0.3) {
                setTimeout(() => fireworks.push(new Firework()), 160);
            }
            lastLaunchTime = ts;
        }

        for (let i = fireworks.length - 1; i >= 0; i--) {
            fireworks[i].update();
            fireworks[i].draw();
            if (fireworks[i].isDone()) fireworks.splice(i, 1);
        }

        requestAnimationFrame(loop);
    }

    requestAnimationFrame(loop);

}());