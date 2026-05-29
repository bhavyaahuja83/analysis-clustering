def analyze_time_slots(group, pickup_threshold=3, duration_threshold=30, min_samples=50):
    result = []

    if 'Day' not in group.columns or 'Hour' not in group.columns:
        return result

    group = group.copy()
    group['Hour'] = group['Hour'].astype(int)

    for day, day_df in group.groupby('Day'):
        hourly = day_df.groupby('Hour').agg(
            PickupRate=('PickupRate', 'mean'),
            AvgDuration=('CallDuration', 'mean'),
            SampleSize=('PickupRate', 'count')
        ).reset_index()

        hourly = hourly[hourly['SampleSize'] >= min_samples]
        if hourly.empty:
            continue

        merged_ranges = []
        current = {'start': None, 'end': None, 'pickup': [], 'duration': []}

        for _, row in hourly.iterrows():
            hr = row['Hour']
            pr, dur = row['PickupRate'], row['AvgDuration']

            if current['start'] is None:
                current.update({'start': hr, 'end': hr, 'pickup': [pr], 'duration': [dur]})
            elif abs(pr - current['pickup'][-1]) <= pickup_threshold and abs(dur - current['duration'][-1]) <= duration_threshold:
                current['end'] = hr
                current['pickup'].append(pr)
                current['duration'].append(dur)
            else:
                merged_ranges.append(current)
                current = {'start': hr, 'end': hr, 'pickup': [pr], 'duration': [dur]}

        if current['start'] is not None:
            merged_ranges.append(current)

        for r in merged_ranges:
            result.append({
                'Day': day,
                'Time': f"{int(r['start']):02d}:00–{int(r['end'])+1:02d}:00",
                'PickupRate': round(sum(r['pickup']) / len(r['pickup']), 2),
                'AvgDuration': round(sum(r['duration']) / len(r['duration']), 2),
                'BestTime': False
            })

    result.sort(key=lambda x: (x['PickupRate'], x['AvgDuration']), reverse=True)
    for i in range(min(3, len(result))):
        result[i]['BestTime'] = True

    return result
