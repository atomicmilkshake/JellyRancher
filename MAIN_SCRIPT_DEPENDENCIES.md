# Main Script Dependencies

**Main Script:** `jelly_rancher_studio.py`

## Direct Dependencies (Level 1)

```
jelly_rancher_studio.py
├── scripts/core/roundup_manager.py
├── scripts/_common/logger.py
├── scripts/ui/welcome_screen.py
├── scripts/ui/styles.py
├── scripts/ui/scan_view.py
├── scripts/ui/scan_results_view.py
├── scripts/ui/analysis_view.py
├── scripts/ui/review_view.py
├── scripts/ui/execution_view.py
├── scripts/ui/subtitles_view.py
└── scripts/core/dialogs/jellyfin_settings_dialog.py
```

## Complete Dependency Tree

### Level 1: Direct Imports

1. **scripts/core/roundup_manager.py** (no JellyRancher dependencies - core module)
2. **scripts/_common/logger.py** (checking...)
3. **scripts/ui/welcome_screen.py**
   - scripts/core/roundup_manager.py
4. **scripts/ui/styles.py** (checking...)
5. **scripts/ui/scan_view.py**
   - scripts/core/file_scanner.py
   - scripts/core/project_manager.py
   - scripts/core/app_config.py
   - scripts/core/inventory_repository.py
   - scripts/core/jellyfin_client.py
   - scripts/core/jellyfin_config.py
   - scripts/core/workers.py
   - scripts/core/roundup_manager.py
6. **scripts/ui/scan_results_view.py** (checking...)
7. **scripts/ui/analysis_view.py**
   - scripts/core/project_manager.py
   - scripts/core/file_scanner.py
   - scripts/core/roundup_manager.py
   - scripts/core/action_plan.py
   - scripts/core/extrapolation_engine.py
   - scripts/ai/ravenmaven_client.py
   - scripts/core/workers.py
   - scripts/core/regex_analysis_worker.py
   - scripts/media/llm_structure_analyzer.py
8. **scripts/ui/review_view.py**
   - scripts/core/project_manager.py
   - scripts/core/file_scanner.py
   - scripts/core/roundup_manager.py
   - scripts/core/action_plan.py
   - scripts/core/action_plan_generator.py
9. **scripts/ui/execution_view.py**
   - scripts/core/project_manager.py
   - scripts/core/roundup_manager.py
   - scripts/core/transaction_manager.py
   - scripts/core/jellyfin_client.py
10. **scripts/ui/subtitles_view.py** (checking...)
11. **scripts/core/dialogs/jellyfin_settings_dialog.py** (checking...)

### Level 2: Secondary Dependencies

**From scan_view.py:**
- scripts/core/file_scanner.py
- scripts/core/project_manager.py
- scripts/core/app_config.py
- scripts/core/inventory_repository.py
- scripts/core/jellyfin_client.py
- scripts/core/jellyfin_config.py
- scripts/core/workers.py

**From analysis_view.py:**
- scripts/core/project_manager.py
- scripts/core/file_scanner.py
- scripts/core/roundup_manager.py
- scripts/core/action_plan.py
- scripts/core/extrapolation_engine.py
- scripts/ai/ravenmaven_client.py
- scripts/core/workers.py
- scripts/core/regex_analysis_worker.py
- scripts/media/llm_structure_analyzer.py

**From review_view.py:**
- scripts/core/project_manager.py
- scripts/core/file_scanner.py
- scripts/core/roundup_manager.py
- scripts/core/action_plan.py
- scripts/core/action_plan_generator.py

**From execution_view.py:**
- scripts/core/project_manager.py
- scripts/core/roundup_manager.py
- scripts/utils/transaction_manager.py
- scripts/core/jellyfin_client.py

### Level 3: Tertiary Dependencies

**From workers.py:**
- scripts/core/file_scanner.py
- scripts/core/roundup_manager.py
- scripts/media/llm_structure_analyzer.py
- scripts/media/regex_structure_analyzer.py
- scripts/media/media_metadata_lookup.py

**From llm_structure_analyzer.py:**
- scripts/ai/ravenmaven_client.py

**From regex_analysis_worker.py:**
- scripts/media/regex_structure_analyzer.py

**From action_plan_generator.py:**
- scripts/core/file_scanner.py
- scripts/core/action_plan.py

**From extrapolation_engine.py:**
- scripts/core/file_scanner.py
- scripts/core/action_plan.py

**From media_metadata_lookup.py:**
- scripts/core/tmdb_backend.py

## Complete List of All Python Scripts Main Script Depends On

### Core Modules
1. scripts/core/roundup_manager.py
2. scripts/core/project_manager.py
3. scripts/core/file_scanner.py
4. scripts/core/action_plan.py
5. scripts/core/action_plan_generator.py
6. scripts/core/extrapolation_engine.py
7. scripts/core/app_config.py
8. scripts/core/inventory_repository.py
9. scripts/core/jellyfin_client.py
10. scripts/core/jellyfin_config.py
11. scripts/core/workers.py
12. scripts/core/regex_analysis_worker.py

### UI Modules
13. scripts/ui/welcome_screen.py
14. scripts/ui/styles.py
15. scripts/ui/scan_view.py
16. scripts/ui/scan_results_view.py
17. scripts/ui/analysis_view.py
18. scripts/ui/review_view.py
19. scripts/ui/execution_view.py
20. scripts/ui/subtitles_view.py
21. scripts/core/dialogs/jellyfin_settings_dialog.py

### Common Modules
22. scripts/_common/logger.py

### AI/Media Modules
23. scripts/ai/ravenmaven_client.py
24. scripts/media/llm_structure_analyzer.py
25. scripts/media/regex_structure_analyzer.py
26. scripts/media/media_metadata_lookup.py

### Utils Modules
27. scripts/utils/transaction_manager.py

### Backend Modules
28. scripts/core/tmdb_backend.py

## Summary

**Total unique Python scripts:** 28 files

**Categories:**
- Core: 12 files
- UI: 9 files
- AI/Media: 4 files
- Common: 1 file
- Utils: 1 file
- Backend: 1 file

## Dependency Chain Visualization

```
jelly_rancher_studio.py
│
├─→ scripts/core/roundup_manager.py (standalone)
│
├─→ scripts/_common/logger.py (standalone)
│
├─→ scripts/ui/welcome_screen.py
│   └─→ scripts/core/roundup_manager.py
│
├─→ scripts/ui/styles.py (standalone)
│
├─→ scripts/ui/scan_view.py
│   ├─→ scripts/core/file_scanner.py
│   ├─→ scripts/core/project_manager.py
│   ├─→ scripts/core/app_config.py
│   ├─→ scripts/core/inventory_repository.py
│   ├─→ scripts/core/jellyfin_client.py
│   ├─→ scripts/core/jellyfin_config.py
│   ├─→ scripts/core/workers.py
│   │   ├─→ scripts/core/file_scanner.py
│   │   ├─→ scripts/core/inventory_repository.py
│   │   ├─→ scripts/media/llm_structure_analyzer.py
│   │   │   └─→ scripts/ai/ravenmaven_client.py
│   │   ├─→ scripts/media/media_metadata_lookup.py
│   │   │   └─→ scripts/core/tmdb_backend.py
│   │   ├─→ scripts/core/action_plan.py
│   │   ├─→ scripts/core/action_plan_generator.py
│   │   │   ├─→ scripts/core/file_scanner.py
│   │   │   └─→ scripts/core/action_plan.py
│   │   └─→ scripts/core/app_config.py
│   └─→ scripts/core/roundup_manager.py
│
├─→ scripts/ui/scan_results_view.py
│   ├─→ scripts/core/file_scanner.py
│   ├─→ scripts/core/project_manager.py
│   ├─→ scripts/core/inventory_repository.py
│   ├─→ scripts/core/jellyfin_config.py
│   └─→ scripts/core/workers.py (see above)
│
├─→ scripts/ui/analysis_view.py
│   ├─→ scripts/core/project_manager.py
│   ├─→ scripts/core/file_scanner.py
│   ├─→ scripts/core/roundup_manager.py
│   ├─→ scripts/core/action_plan.py
│   ├─→ scripts/core/extrapolation_engine.py
│   │   ├─→ scripts/core/file_scanner.py
│   │   └─→ scripts/core/action_plan.py
│   ├─→ scripts/ai/ravenmaven_client.py
│   ├─→ scripts/core/workers.py (see above)
│   ├─→ scripts/core/regex_analysis_worker.py
│   │   └─→ scripts/media/regex_structure_analyzer.py
│   └─→ scripts/media/llm_structure_analyzer.py (see above)
│
├─→ scripts/ui/review_view.py
│   ├─→ scripts/core/project_manager.py
│   ├─→ scripts/core/file_scanner.py
│   ├─→ scripts/core/roundup_manager.py
│   ├─→ scripts/core/action_plan.py
│   └─→ scripts/core/action_plan_generator.py (see above)
│
├─→ scripts/ui/execution_view.py
│   ├─→ scripts/core/project_manager.py
│   ├─→ scripts/core/roundup_manager.py
│   ├─→ scripts/utils/transaction_manager.py
│   └─→ scripts/core/jellyfin_client.py
│
├─→ scripts/ui/subtitles_view.py
│   └─→ scripts/core/project_manager.py
│
└─→ scripts/core/dialogs/jellyfin_settings_dialog.py (standalone)
```

