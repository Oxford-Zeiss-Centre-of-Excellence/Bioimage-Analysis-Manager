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
    height: 34;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#dialog .header {
    text-align: center;
    text-style: bold;
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

#artifact_list {
    height: 1fr;
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
    align: center middle;
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
"""
