# TODO: Fix Avatar Modal, Download Bug, Redesign CSS/HTML Templates, Add Missing CSS, Restore Design

## 1. Fix Download Bug for Finished Competitions
- [x] Update finished_event route in ltta.py to handle POST download request
- [x] Add create_event_card function in downloads.py
- [x] Update event_card.html template for proper PDF generation

## 2. Add Missing CSS Files
- [x] Create static/styles/events.css for templates/events.html
- [x] Create static/styles/finished_event.css for templates/finished_event.html
- [x] Create static/styles/event.css for templates/event.html (if not exists)
- [x] Create static/styles/ratings.css for templates/ratings.html (if not exists)
- [x] Create static/styles/login.css for templates/login.html
- [x] Create static/styles/registration.css for templates/registration.html
- [x] Create static/styles/verification.css for templates/verification.html
- [x] Create static/styles/admin_members.css for templates/admin/members.html
- [x] Create static/styles/admin_profile_admin_view.css for templates/admin/edit_profile_admin_view.html

## 3. Redesign CSS and HTML Templates
- [ ] Standardize CSS variables across all files (--font-size--, --background-color--, --text-color--, --golden--, --lavender--)
- [ ] Add portrait orientation media queries to all CSS files
- [ ] Improve layouts, spacing, and visual consistency
- [ ] Update HTML templates for better structure and accessibility
- [ ] Remove duplicated CSS code
- [ ] Ensure responsive design for mobile/tablet

## 4. Avatar Change Modal Improvements
- [ ] Ensure modal overlays properly with z-index
- [ ] Improve preview and cropping UI in edit_profile.html and edit_profile.css
- [ ] Test avatar upload and cropping functionality

## 5. Restore Previous Design
- [ ] Apply consistent golden/lavender theme across all pages
- [ ] Ensure all pages have similar border-radius, padding, and styling
- [ ] Update navigation and buttons for consistency

## Followup Steps
- [ ] Test downloads and avatar modal functionality
- [ ] Verify responsive design on different screen sizes
- [ ] Run the app to check for errors
- [ ] Test all forms and interactions
