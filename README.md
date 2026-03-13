# Robo Nurse Hackathon

A hackathon project focused on building a robotic nurse assistant.

## Getting Started

### On Raspberry Pi

1. Clone and enter the project:
   ```bash
   cd ~/robo_nurse_hackathon
   git pull origin main
   ```

2. Create `.env` with your smallest.ai API key:
   ```bash
   echo 'SMALLEST_API_KEY=your_key_here
   TARGET_LANGUAGE=english' > .env
   ```

3. Run (suppress ALSA warnings with `2>/dev/null`):
   ```bash
   source venv/bin/activate && python3 transcribe.py 2>/dev/null
   ```

4. Press **r** to start recording, speak, then press **r** to stop and save.

## Tech Stack

*To be determined.*

## Team

Built during a hackathon by [PaiKingDuck555](https://github.com/PaiKingDuck555).

## License

This project is open source. See [LICENSE](LICENSE) for details.
