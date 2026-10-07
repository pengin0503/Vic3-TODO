"""Audit, compare, build and safely publish a probe in the user's mod folder."""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
try:
    from tools.audit_vanilla import audit_archive,audit_game,compare_reports,write_evidence
    from tools.build_probe import build_probe,validate_output,guard_output
    from tools.render_capability_matrix import render_matrix
except ModuleNotFoundError:
    from audit_vanilla import audit_archive,audit_game,compare_reports,write_evidence
    from build_probe import build_probe,validate_output,guard_output
    from render_capability_matrix import render_matrix
ROOT=Path(__file__).resolve().parents[1]

def publish_install(dist,mod_root):
    dist=Path(dist).resolve();mod_root=Path(mod_root).resolve();target=mod_root/'Vic3TODOProbe';descriptor=mod_root/'Vic3TODOProbe.mod'
    if target.exists():
        md=target/'.metadata/metadata.json'
        if target.is_symlink() or not md.is_file() or json.loads(md.read_text('utf-8')).get('id')!='vic3_todo_probe':raise ValueError('Refusing to replace unrelated mod directory')
    if descriptor.exists() and (descriptor.is_symlink() or 'Vic3 TODO Phase 0 Probe' not in descriptor.read_text('utf-8-sig')):
        raise ValueError('Refusing to replace unrelated mod descriptor')
    if target==dist or target in dist.parents or dist in target.parents:raise ValueError('Install destination overlaps build source')
    validate_output(dist)
    mod_root.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.vic3_todo_install_',dir=mod_root));backup=None
    old_descriptor=descriptor.read_bytes() if descriptor.exists() else None
    descriptor_stage=stage.parent/(stage.name+'.mod')
    try:
        shutil.copytree(dist,stage,dirs_exist_ok=True);validate_output(stage)
        path=target.as_posix()
        if '"' in path or '\n' in path or '\r' in path:raise ValueError('Invalid descriptor path')
        version=json.loads((stage/'.metadata/metadata.json').read_text('utf-8'))['version']
        descriptor_stage.write_text(f'name="Vic3 TODO Phase 0 Probe"\nversion="{version}"\nsupported_version="1.14.*"\npath="{path}"\n',encoding='utf-8')
        if target.exists():
            backup=Path(tempfile.mkdtemp(prefix='.vic3_todo_previous_',dir=mod_root));backup.rmdir();os.replace(target,backup)
        try:
            os.replace(stage,target);os.replace(descriptor_stage,descriptor)
        except BaseException:
            if target.exists():shutil.rmtree(target)
            if backup is not None:os.replace(backup,target);backup=None
            if old_descriptor is not None:descriptor.write_bytes(old_descriptor)
            elif descriptor.exists():descriptor.unlink()
            raise
        if backup is not None:shutil.rmtree(backup)
    finally:
        if stage.exists():shutil.rmtree(stage)
        if descriptor_stage.exists():descriptor_stage.unlink()
    return target

def preflight_destinations(game_dir,user_data_dir,source_archive):
    """Validate every writing/replacing path before auditing or making directories."""
    generated=ROOT/'research/generated'
    destinations=[generated/'installed-api-evidence.json',generated/'source-comparison.json',generated/'installed-capability-matrix.md',ROOT/'dist/Vic3TODOProbe',user_data_dir/'mod/Vic3TODOProbe',user_data_dir/'mod/Vic3TODOProbe.mod']
    if source_archive:destinations.append(generated/'installed-archive-evidence.json')
    protected=[game_dir]
    if source_archive:protected.append(Path(source_archive).resolve())
    for destination in destinations:
        if destination.is_symlink():raise ValueError('Install output must not be a symlink')
        dest=destination.resolve()
        for original in protected:
            if dest==original or dest in original.parents or (original.is_dir() and dest.is_relative_to(original)):
                raise ValueError('Install output overlaps read-only game or source archive: '+str(destination))

def install(game_dir,user_data_dir,source_archive=None):
    game_dir=Path(game_dir).resolve();user_data_dir=Path(user_data_dir).resolve()
    if not (game_dir/'binaries/victoria3.exe').is_file():raise ValueError('GameDir must be full Victoria 3 installation root')
    preflight_destinations(game_dir,user_data_dir,source_archive)
    if user_data_dir==game_dir or user_data_dir.is_relative_to(game_dir) or game_dir.is_relative_to(user_data_dir):raise ValueError('User mod destination overlaps installed game')
    generated=ROOT/'research/generated';archive_path=generated/'phase0-api-evidence.json'
    if source_archive:
        archive=audit_archive(Path(source_archive));write_evidence(archive,generated/'installed-archive-evidence.json')
    else:
        archive=json.loads(archive_path.read_text('utf-8'))
    installed=audit_game(game_dir);evidence=generated/'installed-api-evidence.json';write_evidence(installed,evidence)
    comparison=compare_reports(archive,installed);write_evidence(comparison,generated/'source-comparison.json')
    (generated/'installed-capability-matrix.md').write_text(render_matrix(installed),encoding='utf-8')
    print(f"Archive/installed: {comparison['overlap_count']} overlaps, {len(comparison['hash_mismatches'])} hash mismatches, {len(comparison['capability_differences'])} capability differences. Details: {generated/'source-comparison.json'}")
    output=ROOT/'dist/Vic3TODOProbe';build_probe(game_dir,evidence,output)
    target=publish_install(output,user_data_dir/'mod')
    keyboard=json.loads((target/'vic3_todo_keyboard_integration.json').read_text('utf-8'))
    print('Direct probe: Ctrl+Shift+T or the TODO probe HUD button. Initialize enabled: '+str(keyboard['initialize_enabled'])+'; Journal registration enabled: '+str(keyboard['register_enabled']))
    print('Installed: '+str(target));print('Enable Vic3 TODO Phase 0 Probe in a separate launcher playset. Verify actual game version 1.14.x. Runtime results remain NOT_TESTED.')
    return target

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',type=Path,required=True);p.add_argument('--user-data-dir',type=Path,required=True);p.add_argument('--source-archive',type=Path)
    args=p.parse_args(argv)
    try:install(args.game_dir,args.user_data_dir,args.source_archive)
    except (ValueError,OSError) as e:p.error(str(e))
    return 0
if __name__=='__main__':raise SystemExit(main())
