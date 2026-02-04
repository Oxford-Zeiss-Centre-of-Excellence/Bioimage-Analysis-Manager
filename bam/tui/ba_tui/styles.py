EXIT_CONFIRM_CSS = """
ExitConfirmScreen {
    align: center middle;
}

#dialog {
    width: auto;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog Static {
    width: auto;
    content-align: center middle;
    margin-bottom: 1;
}

#dialog #button_row {
    width: auto;
    height: auto;
    align: center middle;
}

#dialog Button {
    margin: 0 1;
}
"""


NEW_MANIFEST_CONFIRM_CSS = """
NewManifestConfirmScreen {
    align: center middle;
}

#dialog {
    width: 50;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog Static {
    width: 100%;
    text-align: center;
    margin-bottom: 1;
}

#dialog #button_row {
    width: 100%;
    height: auto;
    align: center middle;
}

#dialog Button {
    margin: 0 1;
}
"""

RESET_CONFIRM_CSS = """
ResetConfirmScreen {
    align: center middle;
}

#dialog {
    width: 50;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog Static {
    width: 100%;
    text-align: center;
    margin-bottom: 1;
}

#dialog #button_row {
    width: 100%;
    height: auto;
    align: center middle;
}

#dialog Button {
    margin: 0 1;
}
"""


DIRECTORY_PICKER_CSS = """
DirectoryPickerScreen {
    align: center middle;
}

#picker {
    width: 80%;
    height: 80%;
    border: heavy $primary;
    background: $surface;
    padding: 1;
}

#picker_buttons {
    height: auto;
    align: right middle;
    margin-top: 1;
}

#selected_path {
    background: $primary-background;
    padding: 0 1;
    margin: 1 0;
}
"""


COLLABORATOR_MODAL_CSS = """
CollaboratorModal {
    align: center middle;
}

#dialog {
    width: 64;
    height: 22;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 15;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog DateSelect {
    width: 1fr;
    height: 3;
    min-height: 3;
    padding: 0 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


DATASET_MODAL_CSS = """
DatasetModal {
    align: center middle;
}

#dialog {
    width: 78;
    height: 90%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 18;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog Checkbox {
    width: 1fr;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}

#source_suggestions,
#local_suggestions {
    height: 8;
    display: none;
    border: solid $primary;
    margin: 0 0 0 18;
}

#source_suggestions.visible,
#local_suggestions.visible {
    display: block;
}
"""

CHANNEL_MODAL_CSS = """
ChannelModal {
    align: center middle;
}

#dialog {
    width: 60;
    height: 22;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 18;
    text-align: right;
    padding-right: 1;
}

#dialog Input {
    width: 1fr;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


HARDWARE_MODAL_CSS = """
HardwareModal {
    align: center middle;
}

#dialog {
    width: 70;
    height: 80%;
    max-height: 40;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog .-hidden {
    display: none;
}

#dialog Label {
    width: 16;
    text-align: right;
    padding-right: 1;
}

#dialog Input {
    width: 1fr;
}

#dialog Checkbox {
    width: 1fr;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


CUSTOM_INPUT_MODAL_CSS = """
CustomInputModal {
    align: center middle;
}

#dialog {
    width: 60;
    height: 16;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 1;
}

#dialog Input {
    width: 100%;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


MILESTONE_MODAL_CSS = """
MilestoneModal {
    align: center middle;
}

#dialog {
    width: 72;
    height: 70%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#milestone_target_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#milestone_target_datepicker_mount.expanded {
    height: 18;
}

#milestone_actual_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#milestone_actual_datepicker_mount.expanded {
    height: 18;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 18;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


SESSION_MODAL_CSS = """
AcquisitionSessionModal {
    align: center middle;
}

#dialog {
    width: 72;
    height: 70%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 18;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


OTHER_LIST_MODAL_CSS = """
OtherListModal {
    align: center middle;
}

#dialog {
    width: 70;
    height: 16;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 1;
    align: right middle;
}

#dialog Label {
    width: 16;
    text-align: right;
    padding-right: 1;
}

#dialog Input {
    width: 1fr;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


FIGURE_NODE_MODAL_CSS = """
FigureNodeModal {
    align: center middle;
}

#dialog {
    width: 64;
    height: 60%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 16;
    text-align: right;
    padding-right: 1;
}

#dialog Input {
    width: 1fr;
}

#dialog TextArea {
    height: 4;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


FIGURE_ELEMENT_MODAL_CSS = """
FigureElementModal {
    align: center middle;
}

#dialog {
    width: 78;
    height: 80%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 16;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog DateSelect {
    width: 1fr;
    height: 3;
    min-height: 3;
    padding: 0 1;
}

#dialog TextArea {
    height: 4;
}

#element_delivery_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#element_delivery_datepicker_mount.expanded {
    height: 18;
}

#output_path_suggestions {
    height: 8;
    display: none;
    border: solid $primary;
    margin: 0 0 0 16;
}

#output_path_suggestions.visible {
    display: block;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}
"""


DELETE_CONFIRM_MODAL_CSS = """
DeleteConfirmModal {
    align: center middle;
}

#dialog {
    width: 52;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    width: 100%;
    text-align: center;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    height: auto;
    align: center middle;
}

#buttons Button {
    margin: 0 1;
}
"""


ARTIFACT_MODAL_CSS = """
ArtifactModal {
    align: center middle;
}

#dialog {
    width: 76;
    height: 70%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 0;
}

#dialog .form-row {
    height: auto;
    margin-bottom: 0;
    align: right middle;
}

#dialog Label {
    width: 18;
    text-align: right;
    padding-right: 1;
}

#dialog Input, #dialog Select {
    width: 1fr;
}

#dialog_scroll {
    height: 1fr;
    margin-bottom: 1;
}

#buttons {
    width: 100%;
    align: center middle;
    margin-top: 0;
    height: auto;
}

#buttons Button {
    margin: 0 1;
}

#artifact_path_suggestions {
    height: 8;
    display: none;
    border: solid $primary;
    margin: 0 0 0 18;
}

#artifact_path_suggestions.visible {
    display: block;
}
"""

APP_CSS = """
#form {
    width: 90%;
    padding: 0 1;
}

.form-row {
    height: auto;
    margin: 0;
    align: left middle;
}

.form-row Label {
    width: 14;
    padding-right: 1;
}

.form-row Input {
    width: 1fr;
}

.form-row Select {
    width: 1fr;
}

.form-row DateSelect {
    width: 1fr;
}

.form-row Button {
    margin-left: 1;
    min-width: 8;
}

.form-row Checkbox {
    margin-left: 1;
}

.section-header {
    margin: 1 0 0 0;
    text-style: bold;
    color: $primary;
}

.form-hint {
    color: $text-muted;
    text-style: italic;
}

.hint-text {
    width: 100%;
    text-align: center;
    color: $text-muted;
    text-style: italic;
    margin-top: 1;
    margin-bottom: 1;
    padding: 0 2;
}

Horizontal {
    align: left middle;
}

Button {
    min-width: 6;
    background: transparent;
    border: none;
    color: $secondary;
}

Button.-primary {
    color: $accent;
}

Button.-success {
    color: $success;
}

Button.-warning {
    color: $warning;
}

Button.-error {
    color: $error;
}

Button.-default {
    color: $text-muted;
}

SelectionList .selection--selected {
    background: $warning;
    color: $text;
}

SelectionList .selection--checked {
    color: $warning;
}

SelectionList .selection--checked .selection--label {
    color: $warning;
}

SelectionList .selection--checked .selection--checkbox {
    color: $warning;
}

SelectionList Checkbox {
    color: $warning;
}


TextArea {
    height: 5;
}

DateSelect {
    height: 3;
    min-height: 3;
}

#log_entries {
    height: 6;
    overflow-y: auto;
    border: solid green;
    padding: 0;
}

Input.valid {
    border: tall $success;
}

Input.invalid {
    border: tall $error;
}

TextArea.valid {
    border: tall $success;
}

TextArea.invalid {
    border: tall $error;
}


#sync_row {
    height: auto;
    margin: 1 0 0 0;
    align: center middle;
}

#sync_btn {
    min-width: 18;
}

#sync_btn.disabled {
    color: $text-muted;
    text-style: dim;
}

#sync_progress {
    width: 20;
    margin-left: 2;
    display: none;
}

#sync_progress.visible {
    display: block;
}

#sync_pct {
    width: 5;
    margin-left: 1;
    display: none;
}

#sync_pct.visible {
    display: block;
}

#dataset_sync_row {
    height: auto;
    margin: 1 0 0 0;
    align: left middle;
}

#path_suggestions {
    height: 8;
    width: 100%;
    display: none;
    border: solid $primary;
    margin: 0 0 0 14;
}

#path_suggestions.visible {
    display: block;
}

#data_sections {
    height: auto;
}

#data_sections.hidden {
    display: none;
}

.hidden {
    display: none;
}

#log_panels {
    height: 1fr;
}

#log_panels ListView {
    height: 1fr;
    border: solid $primary;
}

#log_controls {
    height: auto;
    margin-top: 0;
}

#idea_form TextArea {
    height: 4;
}

#manifest_sections {
    height: 1fr;
}

#idea_list_panel {
    width: 30%;
}

#idea_form {
    width: 70%;
}

/* Center containers for tables */
#people_form Center,
#data_form Center,
#acquisition_form Center,
#timeline_form Center,
#hardware_form Center {
    height: auto;
    width: 100%;
}

#collaborators_table {
    height: 10;
    width: 90%;
}

#collaborator_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#collaborator_actions Button {
    min-width: 14;
    margin-right: 1;
}

#datasets_table {
    height: 10;
    width: 90%;
}

#dataset_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#dataset_actions Button {
    min-width: 14;
    margin-right: 1;
}

#channels_table {
    height: 10;
    width: 90%;
}

#hardware_table {
    height: 8;
    width: 90%;
}

#hardware_actions {
    align: center middle;
}

#milestone_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#remove_milestone {
    min-width: 16;
}

#milestones_table {
    height: 10;
    width: 90%;
}

#acquisition_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#acquisition_table {
    height: 10;
    width: 90%;
}

#channel_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#artifacts_table {
    height: 10;
    width: 90%;
}

#artifact_actions {
    align: center middle;
    height: auto;
    margin-top: 1;
}

#artifact_actions Button {
    min-width: 14;
    margin-right: 1;
}

#session_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#session_datepicker_mount.expanded {
    height: 18;
}

#billing_form DateSelect {
    width: 1fr;
    height: 3;
    min-height: 3;
    padding: 0 1;
}

#billing_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#billing_datepicker_mount.expanded {
    height: 18;
}

#archive_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#archive_datepicker_mount.expanded {
    height: 18;
}

#billing_dates_row {
    height: auto;
}

#billing_dates_row .form-row {
    width: 1fr;
    height: auto;
}

#billing_dates_row Label {
    width: 12;
}

#languages_actions,
#software_actions,
#cluster_packages_actions {
    align: center top;
    height: auto;
}

#languages_list,
#software_list,
#cluster_packages_list {
    height: 8;
}

#method_preview {
    height: 1fr;
    border: solid $primary;
    padding: 1;
}

#method_path_suggestions {
    height: 6;
    width: 100%;
    display: none;
    border: solid $primary;
    margin: 0 0 0 14;
}

#method_path_suggestions.visible {
    display: block;
}

#archive_location_suggestions {
    height: 8;
    width: 100%;
    display: none;
    border: solid $primary;
    margin: 0 0 0 14;
}

#archive_location_suggestions.visible {
    display: block;
}

/* Figure tree container */
#figure_tree_container {
    height: 30;
    width: 100%;
    margin-bottom: 1;
}

#figure_tree {
    width: 50%;
    height: 100%;
    border: solid $primary;
}

#figure_info_box {
    width: 50%;
    height: 100%;
    border: solid $primary;
    padding: 1;
    margin-left: 1;
}

#figure_info_content {
    width: 100%;
    text-align: left;
}

#figure_actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 1;
}

#figure_actions Button {
    margin: 0 1;
}

/* Placeholder tabs styling */
#hub_placeholder,
#idea_placeholder {
    width: 100%;
    height: 1fr;
    align: center middle;
}

.placeholder-title {
    text-align: center;
    text-style: bold;
    color: $text-muted;
    margin-bottom: 1;
}

.placeholder-description {
    text-align: center;
    color: $text-muted;
    text-style: italic;
}
"""


# =============================================================================
# Worklog Modals
# =============================================================================

TASK_MODAL_CSS = """
TaskModal {
    align: center middle;
}

#dialog {
    width: 80;
    height: auto;
    max-height: 90%;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    width: 100%;
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#dialog_scroll {
    width: 100%;
    height: 1fr;
    max-height: 60;
    overflow-y: scroll;
    scrollbar-gutter: stable;
}

#dialog .form-row {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

#dialog .form-row Label {
    width: 20;
    content-align: right middle;
    margin-right: 2;
}

#dialog .form-row Input {
    width: 1fr;
}

#dialog .form-row Select {
    width: 1fr;
}

#dialog .-hidden {
    display: none;
}

#dialog .button-row {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1;
}

#dialog Button {
    margin: 0 1;
}
"""


# =============================================================================
# Log Tab
# =============================================================================

LOG_TAB_CSS = """
#log {
    padding: 1 2;
}

#log_tree_container {
    height: 1fr;
    width: 100%;
    margin-bottom: 1;
    overflow: hidden;
}

#log_dashboard {
    width: 50%;
    min-width: 0;
    max-width: 50%;
    height: 100%;
    border: solid $primary;
    padding: 1;
    scrollbar-gutter: stable;
}

#dashboard_sessions_container {
    width: 100%;
    height: 1fr;
    overflow-y: auto;
    scrollbar-gutter: stable;
}

.session-box {
    width: 100%;
    border: solid $primary;
    padding: 1;
    margin-bottom: 1;
    background: $panel;
    min-height: 8;
    height: auto;
}

.session-header {
    width: 100%;
    text-style: bold;
    color: $success;
    margin-bottom: 1;
}

.session-details {
    width: 100%;
    color: $text-muted;
    margin-bottom: 1;
}

.session-buttons {
    width: 100%;
    height: auto;
    margin-top: 1;
}

.session-btn {
    margin-right: 1;
}

.muted-text {
    color: $text-muted;
    text-style: italic;
    padding: 1;
}

#dashboard_status {
    width: 100%;
    text-style: bold;
    margin-bottom: 1;
}

#dashboard_status.active-session {
    text-style: bold;
    color: $success;
}

#dashboard_details {
    width: 100%;
    margin-bottom: 1;
    color: $text-muted;
}

#dashboard_buttons {
    width: 100%;
    height: auto;
    align: left middle;
}

#dashboard_buttons Button {
    margin-right: 1;
}

#task_tree {
    width: 50%;
    min-width: 0;
    max-width: 50%;
    height: 100%;
    border: solid $primary;
    overflow-x: hidden;
}


#log_actions {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 1;
}

#log_actions Button {
    margin: 0 1;
    min-width: 18;
}


#log_history_toggle {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

.status-message {
    width: 100%;
    margin-top: 1;
    text-align: center;
    color: $warning;
}

.session-normal {
    color: $success;
}

.session-long {
    color: $warning;
}

.session-active {
    color: $accent;
}

.session-problem {
    color: $error;
}
"""


EDIT_SESSION_MODAL_CSS = """
EditSessionModal {
    align: center middle;
}

#dialog {
    width: 70;
    height: auto;
    max-height: 90%;
    border: thick $primary;
    background: $surface;
}

#dialog .header {
    width: 100%;
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#punch_in_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#punch_in_datepicker_mount.expanded {
    height: 18;
}

#punch_out_datepicker_mount {
    height: 0;
    overflow: hidden;
}

#punch_out_datepicker_mount.expanded {
    height: 18;
}

#dialog_scroll {
    width: 100%;
    height: 1fr;
    max-height: 60;
    padding: 1 2;
}

#dialog .form-row {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

#dialog .form-row Label {
    width: 15;
    content-align: right middle;
    margin-right: 2;
}

#dialog .form-row Input {
    width: 1fr;
}

#dialog .section-label {
    width: 100%;
    margin-top: 1;
    margin-bottom: 1;
    text-style: bold;
    color: $accent;
}

#dialog #task_name_display {
    width: 1fr;
    text-style: italic;
}

#dialog #session_note {
    width: 100%;
    height: 8;
}

#dialog .error-message {
    width: 100%;
    color: $error;
    margin-top: 1;
    text-align: center;
}

#dialog .button-row {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1;
}

#dialog Button {
    margin: 0 1;
}
"""


SESSION_NOTE_MODAL_CSS = """
SessionNoteModal {
    align: center middle;
}

#dialog {
    width: 60;
    height: auto;
    max-height: 90%;
    border: thick $primary;
    background: $surface;
}

#dialog .header {
    width: 100%;
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#dialog_scroll {
    width: 100%;
    height: 1fr;
    max-height: 40;
    padding: 1 2;
}

#dialog .section-label {
    width: 100%;
    margin-bottom: 1;
}

#dialog #session_note {
    width: 100%;
    height: 10;
}

#dialog .button-row {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1;
}

#dialog Button {
    margin: 0 1;
}
"""
