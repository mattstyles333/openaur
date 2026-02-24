FROM archlinux:base-devel AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm --needed \
        python \
        python-pip \
        git \
        sudo \
        tmux \
        sqlite \
        curl \
        base-devel \
        gcc \
        make \
        rust \
        && \
    pacman -Scc --noconfirm && \
    rm -rf /var/cache/pacman/pkg/* /tmp/*

RUN useradd -m -G wheel -s /bin/bash aura && \
    echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER aura
WORKDIR /home/aura

RUN git clone https://aur.archlinux.org/yay-bin.git /tmp/yay-bin && \
    cd /tmp/yay-bin && \
    makepkg -si --noconfirm && \
    rm -rf /tmp/yay-bin && \
    yay -Scc --noconfirm

COPY --chown=aura:aura aura-pkg-add.sh /home/aura/.local/bin/aura-pkg-add
RUN chmod +x /home/aura/.local/bin/aura-pkg-add

COPY --chown=aura:aura pyproject.toml README.md /home/aura/
RUN pip install --user --break-system-packages --no-cache-dir /home/aura/

COPY --chown=aura:aura src/ /home/aura/app/src/
COPY --chown=aura:aura actions/ /home/aura/app/actions/

WORKDIR /home/aura/app

FROM archlinux:base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm --needed \
        python \
        python-pip \
        git \
        sudo \
        tmux \
        sqlite \
        curl \
        && \
    pacman -Scc --noconfirm && \
    rm -rf /var/cache/pacman/pkg/* /tmp/*

COPY --from=builder /etc/sudoers /etc/sudoers
COPY --from=builder /home/aura /home/aura

RUN useradd -u 1000 -m -G wheel -s /bin/bash aura 2>/dev/null || true && \
    chown -R aura:aura /home/aura

USER aura
WORKDIR /home/aura/app

# Create data directory for SQLite
RUN mkdir -p /home/aura/app/data && chown aura:aura /home/aura/app/data

ENV PATH="/home/aura/.local/bin:$PATH"
ENV OPENROUTER_API_KEY=""
ENV DATABASE_URL="sqlite:///home/aura/app/data/openaura.db"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
