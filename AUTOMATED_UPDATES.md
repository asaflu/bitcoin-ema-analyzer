# Automated Data Collection System

## Overview

The Bitcoin 1-minute OHLCV data is automatically updated every 4 hours using a scheduled cron job. This ensures your database stays current without manual intervention.

## System Components

### 1. Update Script (`scripts/update_data.py`)
- Checks the latest timestamp in the database
- Fetches missing data from Binance API
- Inserts new records into the database
- Logs all operations

### 2. Shell Wrapper (`scripts/run_update.sh`)
- Activates the Python virtual environment
- Runs the update script
- Redirects output to log file

### 3. Cron Job
- Runs every 4 hours at the top of the hour (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
- Schedule: `0 */4 * * *`

## Monitoring

### Check Logs
```bash
# View latest update log
tail -50 logs/update_data.log

# View all logs
cat logs/update_data.log

# Monitor in real-time
tail -f logs/update_data.log
```

### Check Cron Status
```bash
# View current cron jobs
crontab -l

# Check if cron is running
ps aux | grep cron
```

### Verify Database Currency
```bash
source venv/bin/activate
python -c "
from database.connection import db
from database.queries import get_latest_timestamp
from datetime import datetime

with db.connection() as conn:
    latest = get_latest_timestamp(conn)
    latest_date = datetime.fromtimestamp(latest/1000)
    now = datetime.now()
    gap = (now.timestamp() * 1000 - latest) / 1000 / 60

    print(f'Latest data: {latest_date}')
    print(f'Current time: {now}')
    print(f'Gap: {gap:.1f} minutes')
"
```

## Manual Updates

### Run Update Immediately
```bash
# From project root
source venv/bin/activate
python scripts/update_data.py
```

### Run via Shell Script
```bash
# From project root
./scripts/run_update.sh
```

## Expected Behavior

### Normal Operation
- **Every 4 hours**: Fetches ~240 minutes (4 hours) of data
- **Success**: Logs show "Successfully added N new records"
- **Up-to-date**: If gap < 1 minute, logs "Database is already up to date"

### Example Log Output
```
======================================================================
AUTOMATED DATA UPDATE - BITCOIN 1-MINUTE OHLCV
======================================================================
Update started at: 2026-02-09 12:00:01
Latest data in database: 2026-02-09 08:00:00
Current time: 2026-02-09 12:00:01
Time gap: 4.00 hours (240 minutes)
Fetching data from 2026-02-09 08:01:00 to 2026-02-09 12:00:01
Successfully added 240 new records
======================================================================
Update completed at: 2026-02-09 12:00:15
======================================================================
```

## Troubleshooting

### Updates Not Running
1. Check if cron is active: `ps aux | grep cron`
2. Check cron job is installed: `crontab -l`
3. Check script permissions: `ls -l scripts/run_update.sh` (should be executable)
4. Check logs for errors: `tail -50 logs/update_data.log`

### API Errors
- **Rate limits**: Script automatically retries with exponential backoff
- **Network issues**: Check internet connection
- **Binance downtime**: Wait for service to resume; updates will catch up

### Database Issues
- **Disk space**: Check available space: `df -h`
- **Permissions**: Ensure write access to `data/` directory
- **Corruption**: Run verification: `python scripts/verify_data.py`

## Disabling Automated Updates

### Temporary Disable (keep cron job)
```bash
# Comment out the job
crontab -e
# Add # at the start of the Bitcoin update line
```

### Permanent Disable (remove cron job)
```bash
# Edit crontab
crontab -e
# Delete the Bitcoin update line, save and exit
```

## Data Retention

The database grows by approximately:
- **Per day**: ~1,440 records (24 hours × 60 minutes)
- **Per month**: ~43,800 records
- **Disk usage**: ~10 MB per month

Current database size can be checked with:
```bash
du -h data/bitcoin_ohlcv.db
```

## Integration with Streamlit App

The Streamlit app (`app.py`) automatically uses the latest data:
- Data is cached for 5 minutes (`@st.cache_data(ttl=300)`)
- To force refresh, restart the app or wait for cache expiration
- Charts will automatically show new data when reloaded

## Maintenance

### Weekly Tasks
- Review logs for errors: `grep ERROR logs/update_data.log`
- Check database size: `du -h data/bitcoin_ohlcv.db`

### Monthly Tasks
- Verify data completeness: `python scripts/verify_data.py`
- Archive old logs: `mv logs/update_data.log logs/update_data_$(date +%Y%m).log`

### As Needed
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Backup database: `cp data/bitcoin_ohlcv.db data/backup_$(date +%Y%m%d).db`

## Support

For issues or questions:
1. Check logs: `logs/update_data.log`
2. Run verification: `python scripts/verify_data.py`
3. Test manual update: `python scripts/update_data.py`
4. Review this documentation
