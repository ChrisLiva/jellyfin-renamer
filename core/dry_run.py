import os


def render_dry_run_movies(main_files, extra_files, target_dir, downmix_audio, print_summary=True):
    """Render dry-run output for movies as a grouped tree.

    Returns (move_count, ffmpeg_count) so callers can aggregate for combined summaries.
    Only prints the summary line if print_summary=True (default).
    """
    move_count = 0
    ffmpeg_count = 0

    # Group operations by movie folder
    groups = {}
    for file_info, target_path in main_files:
        rel = os.path.relpath(target_path, target_dir)
        parts = rel.split(os.sep)
        folder = parts[0]
        filename = os.sep.join(parts[1:])
        if folder not in groups:
            groups[folder] = []
        label = "[COPY + FFMPEG]" if downmix_audio else "[MOVE]"
        if downmix_audio:
            ffmpeg_count += 1
        else:
            move_count += 1
        groups[folder].append((filename, file_info["path"], label))

    for file_info, target_path in extra_files:
        rel = os.path.relpath(target_path, target_dir)
        parts = rel.split(os.sep)
        folder = parts[0]
        filename = os.sep.join(parts[1:])
        if folder not in groups:
            groups[folder] = []
        move_count += 1
        groups[folder].append((filename, file_info["path"], "[MOVE]"))

    # Print grouped tree
    for folder in sorted(groups.keys()):
        print(f"{folder}/")
        entries = groups[folder]
        # Collect subfolder structure
        subfolders = {}
        direct_files = []
        for filename, source, label in entries:
            parts = filename.split(os.sep)
            if len(parts) > 1:
                subfolder = parts[0]
                subfile = os.sep.join(parts[1:])
                if subfolder not in subfolders:
                    subfolders[subfolder] = []
                subfolders[subfolder].append((subfile, source, label))
            else:
                direct_files.append((filename, source, label))

        for filename, source, label in direct_files:
            print(f"  {filename}  <-  {source}  {label}")

        for subfolder in sorted(subfolders.keys()):
            print(f"  {subfolder}/")
            for subfile, source, label in subfolders[subfolder]:
                print(f"    {subfile}  <-  {source}  {label}")

    if print_summary:
        print_dry_run_summary(move_count, ffmpeg_count)

    return move_count, ffmpeg_count


def render_dry_run_tv(main_files, extra_files, target_dir, downmix_audio, print_summary=True):
    """Render dry-run output for TV shows as a grouped tree.

    Returns (move_count, ffmpeg_count) so callers can aggregate for combined summaries.
    Only prints the summary line if print_summary=True (default).
    """
    move_count = 0
    ffmpeg_count = 0

    # Group by series -> season
    series = {}
    all_ops = []
    for file_info, target_path in main_files:
        label = "[COPY + FFMPEG]" if downmix_audio else "[MOVE]"
        if downmix_audio:
            ffmpeg_count += 1
        else:
            move_count += 1
        all_ops.append((file_info, target_path, label))

    for file_info, target_path in extra_files:
        move_count += 1
        all_ops.append((file_info, target_path, "[MOVE]"))

    for file_info, target_path, label in all_ops:
        rel = os.path.relpath(target_path, target_dir)
        parts = rel.split(os.sep)
        series_name = parts[0]
        season_name = parts[1] if len(parts) > 1 else "Season 01"
        filename = os.sep.join(parts[2:]) if len(parts) > 2 else parts[-1]

        if series_name not in series:
            series[series_name] = {}
        if season_name not in series[series_name]:
            series[series_name][season_name] = []
        series[series_name][season_name].append((filename, file_info["path"], label))

    for series_name in sorted(series.keys()):
        print(f"{series_name}/")
        for season_name in sorted(series[series_name].keys()):
            print(f"  {season_name}/")
            entries = series[series_name][season_name]
            # Separate direct files from subfolder files (extras)
            direct = []
            subfolders = {}
            for filename, source, label in entries:
                parts = filename.split(os.sep)
                if len(parts) > 1:
                    sf = parts[0]
                    sf_file = os.sep.join(parts[1:])
                    if sf not in subfolders:
                        subfolders[sf] = []
                    subfolders[sf].append((sf_file, source, label))
                else:
                    direct.append((filename, source, label))

            for filename, source, label in direct:
                print(f"    {filename}  <-  {source}  {label}")

            for sf in sorted(subfolders.keys()):
                print(f"    {sf}/")
                for sf_file, source, label in subfolders[sf]:
                    print(f"      {sf_file}  <-  {source}  {label}")

    if print_summary:
        print_dry_run_summary(move_count, ffmpeg_count)

    return move_count, ffmpeg_count


def print_dry_run_summary(move_count, ffmpeg_count):
    """Print summary line. Public so organize_mixed_content can call it for combined totals."""
    parts = []
    if move_count:
        parts.append(f"{move_count} file{'s' if move_count != 1 else ''} would be moved")
    if ffmpeg_count:
        parts.append(
            f"{ffmpeg_count} file{'s' if ffmpeg_count != 1 else ''} would be copied + processed with FFmpeg"
        )
    if parts:
        print(f"\n{', '.join(parts)}")
    else:
        print("\nNo files to process")
