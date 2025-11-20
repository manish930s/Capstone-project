document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const eventsList = document.getElementById('events-list');
    const recentChatsList = document.getElementById('recent-chats-list');
    const newChatBtn = document.getElementById('new-chat-btn');

    // Tasks View Elements
    const navChat = document.getElementById('nav-chat');
    const navTasks = document.getElementById('nav-tasks');
    const navDashboard = document.getElementById('nav-dashboard');
    const navQuizzes = document.getElementById('nav-quizzes');
    const chatArea = document.querySelector('.chat-area');
    const tasksArea = document.getElementById('tasks-view');
    const dashboardArea = document.getElementById('dashboard-view');
    const quizzesArea = document.getElementById('quizzes-view');
    const scheduledTasksList = document.getElementById('scheduled-tasks-list');
    const manualTasksList = document.getElementById('manual-tasks-list');
    const newTaskInput = document.getElementById('new-task-input');
    const addTaskBtn = document.getElementById('add-task-btn');

    // Quiz View Elements
    const quizSelection = document.getElementById('quiz-selection');
    const quizContent = document.getElementById('quiz-content');
    const backToQuizSelection = document.getElementById('back-to-quiz-selection');

    let currentSessionId = null;

    // Initial load
    fetchEvents();
    loadSessions();
    loadManualTasks();
    loadDashboard();

    // Event Listeners
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }

    function createNewChat() {
        currentSessionId = null;
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        if (userInput) {
            userInput.value = '';
        }
        // Use window.switchView to ensure it works from anywhere
        if (typeof switchView === 'function') {
            switchView('chat');
        } else if (window.switchView) {
            window.switchView('chat');
        }
    }

    // Expose to window for inline onclick handlers
    window.startNewChat = createNewChat;


    if (navChat) {
        navChat.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('chat');
        });
    }

    if (navTasks) {
        navTasks.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('tasks');
        });
    }

    if (navDashboard) {
        navDashboard.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('dashboard');
        });
    }

    if (navQuizzes) {
        navQuizzes.addEventListener('click', (e) => {
            e.preventDefault();
            switchView('quizzes');
        });
    }

    if (backToQuizSelection) {
        backToQuizSelection.addEventListener('click', () => {
            quizContent.classList.add('hidden');
            quizSelection.classList.remove('hidden');
        });
    }

    // Quiz mode selection
    document.querySelectorAll('.quiz-mode-card').forEach(card => {
        const startBtn = card.querySelector('.quiz-start-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                const mode = card.getAttribute('data-mode');
                selectQuizMode(mode);
            });
        }
    });

    if (addTaskBtn) {
        addTaskBtn.addEventListener('click', addManualTask);
    }

    if (newTaskInput) {
        newTaskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addManualTask();
            }
        });
    }

    const refreshBtn = document.getElementById('refresh-calendar');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchEvents);
    }

    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            userInput.value = '';

            // Show thinking indicator
            const thinkingMsg = showThinking();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message,
                        session_id: currentSessionId
                    })
                });

                // Remove thinking indicator
                if (thinkingMsg) thinkingMsg.remove();

                const data = await response.json();

                if (data.session_id) {
                    currentSessionId = data.session_id;
                }

                if (data.response) {
                    addMessage(data.response, 'agent');
                }

                loadSessions();
                fetchEvents();
            } catch (error) {
                // Remove thinking indicator
                if (thinkingMsg) thinkingMsg.remove();
                console.error('Error:', error);
                addMessage('Sorry, something went wrong.', 'agent');
            }
        });
    }

    function showThinking() {
        if (!chatMessages) return null;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message agent thinking';

        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="content">
                Thinking<div class="thinking-dots"><span></span><span></span><span></span></div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', uploadFile);
    }

    async function uploadFile() {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                addMessage(`✓ File "${file.name}" uploaded successfully!`, 'agent');
            } else {
                addMessage(`✗ Upload failed: ${data.error}`, 'agent');
            }
        } catch (error) {
            console.error('Upload error:', error);
            addMessage('✗ Upload failed.', 'agent');
        }

        fileInput.value = '';
    }

    function addMessage(content, sender) {
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.innerHTML = sender === 'user' ?
            '<i class="fa-solid fa-user"></i>' :
            '<i class="fa-solid fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('content');

        const lines = content.split('\n');
        lines.forEach(line => {
            const p = document.createElement('p');
            p.textContent = line;
            contentDiv.appendChild(p);
        });

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function fetchEvents() {
        if (!eventsList) return;

        try {
            const response = await fetch('/events');
            const data = await response.json();

            eventsList.innerHTML = '';

            // Also clear the scheduled tasks list if it exists
            if (scheduledTasksList) {
                scheduledTasksList.innerHTML = '';
            }

            let hasEventsToday = false;

            if (data.events && data.events.length > 0) {
                const today = new Date();

                data.events.forEach(event => {
                    // 1. Populate Sidebar List (All upcoming events)
                    const eventItem = document.createElement('div');
                    eventItem.classList.add('event-item');

                    const startDate = new Date(event.start.dateTime || event.start.date);
                    const timeStr = startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                    // Check if event is today
                    const isToday = startDate.getDate() === today.getDate() &&
                        startDate.getMonth() === today.getMonth() &&
                        startDate.getFullYear() === today.getFullYear();

                    eventItem.innerHTML = `
                        <div class="event-time">${timeStr}</div>
                        <div class="event-title">${event.summary}</div>
                    `;
                    eventsList.appendChild(eventItem);

                    // 2. Populate Scheduled Tasks List (Only Today's events)
                    if (scheduledTasksList && isToday) {
                        hasEventsToday = true;
                        const taskItem = document.createElement('div');
                        taskItem.classList.add('task-item');

                        const isCompleted = event.summary.startsWith("✅ ");
                        if (isCompleted) {
                            taskItem.classList.add('completed');
                        }

                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.classList.add('task-checkbox');
                        checkbox.checked = isCompleted;
                        checkbox.onclick = () => window.toggleEventCompletion(event.id, event.summary);

                        const taskContent = document.createElement('div');
                        taskContent.classList.add('task-content');

                        const taskText = document.createElement('div');
                        taskText.classList.add('task-text');
                        taskText.textContent = event.summary;
                        if (isCompleted) {
                            taskText.style.textDecoration = 'line-through';
                            taskText.style.color = 'var(--text-secondary)';
                        }

                        const taskMeta = document.createElement('div');
                        taskMeta.classList.add('task-meta');
                        taskMeta.textContent = `${timeStr} • ${event.description || 'Google Calendar Event'}`;

                        taskContent.appendChild(taskText);
                        taskContent.appendChild(taskMeta);

                        taskItem.appendChild(checkbox);
                        taskItem.appendChild(taskContent);

                        // Add delete button for completed tasks
                        if (isCompleted) {
                            const deleteBtn = document.createElement('button');
                            deleteBtn.classList.add('delete-task-btn');
                            deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
                            deleteBtn.title = 'Delete event';
                            deleteBtn.onclick = () => window.deleteCalendarEvent(event.id, event.summary);
                            taskItem.appendChild(deleteBtn);
                        }

                        scheduledTasksList.appendChild(taskItem);
                    }
                });
            }

            // Handle empty states
            if (eventsList.children.length === 0) {
                eventsList.innerHTML = '<div class="empty-state">No upcoming events</div>';
            }

            if (scheduledTasksList && !hasEventsToday) {
                scheduledTasksList.innerHTML = '<div class="empty-state">No events scheduled for today.</div>';
            }

        } catch (error) {
            console.error('Error fetching events:', error);
            eventsList.innerHTML = '<div class="empty-state">Failed to load events</div>';
            if (scheduledTasksList) {
                scheduledTasksList.innerHTML = '<div class="empty-state">Failed to load events</div>';
            }
        }
    }

    // Expose globally
    window.toggleEventCompletion = async function (eventId, currentSummary) {
        try {
            const response = await fetch('/mark_event_complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: eventId, summary: currentSummary })
            });

            const data = await response.json();
            if (data.ok) {
                fetchEvents(); // Refresh list
            } else {
                alert('Failed to update task');
            }
        } catch (error) {
            console.error('Error updating task:', error);
        }
    };

    // Delete calendar event
    window.deleteCalendarEvent = async function (eventId, eventSummary) {
        if (!confirm(`Are you sure you want to delete "${eventSummary}"?`)) {
            return;
        }

        try {
            const response = await fetch('/delete_calendar_event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: eventId })
            });

            const data = await response.json();
            if (data.ok) {
                fetchEvents(); // Refresh list
            } else {
                alert('Failed to delete event');
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            alert('Failed to delete event');
        }
    };

    async function loadSessions() {
        if (!recentChatsList) return;

        try {
            const response = await fetch('/sessions');
            const sessions = await response.json();

            recentChatsList.innerHTML = '';

            sessions.forEach(session => {
                const chatItem = document.createElement('div');
                chatItem.classList.add('chat-item');
                if (session.id === currentSessionId) {
                    chatItem.classList.add('active');
                }

                const title = document.createElement('div');
                title.classList.add('chat-title');
                title.textContent = session.title || 'New Chat';
                title.onclick = () => loadSession(session.id);

                const deleteBtn = document.createElement('button');
                deleteBtn.classList.add('delete-chat-btn');
                deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                };

                chatItem.appendChild(title);
                chatItem.appendChild(deleteBtn);
                recentChatsList.appendChild(chatItem);
            });
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    async function deleteSession(sessionId) {
        try {
            await fetch(`/delete_session/${sessionId}`, { method: 'DELETE' });
            if (sessionId === currentSessionId) {
                createNewChat();
            }
            loadSessions();
        } catch (error) {
            console.error('Error deleting session:', error);
        }
    }

    async function loadSession(sessionId) {
        if (sessionId === currentSessionId) return;

        try {
            const response = await fetch(`/history/${sessionId}`);
            const history = await response.json();

            currentSessionId = sessionId;
            if (chatMessages) {
                chatMessages.innerHTML = '';

                history.forEach(msg => {
                    const sender = msg.role === 'model' ? 'agent' : 'user';
                    addMessage(msg.content, sender);
                });
            }

            loadSessions();
        } catch (error) {
            console.error('Error loading session:', error);
        }
    }

    function switchView(view) {
        if (view === 'chat') {
            chatArea.classList.remove('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.add('active');
            navTasks.classList.remove('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.remove('active');
        } else if (view === 'tasks') {
            chatArea.classList.add('hidden');
            tasksArea.classList.remove('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.remove('active');
            navTasks.classList.add('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.remove('active');
            fetchEvents();
            loadManualTasks();
        } else if (view === 'dashboard') {
            chatArea.classList.add('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.remove('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.remove('active');
            navTasks.classList.remove('active');
            navDashboard.classList.add('active');
            navQuizzes.classList.remove('active');
            loadDashboard();
        } else if (view === 'quizzes') {
            chatArea.classList.add('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.remove('hidden');
            navChat.classList.remove('active');
            navTasks.classList.remove('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.add('active');
            quizSelection.classList.remove('hidden');
            quizContent.classList.add('hidden');
        }
    }

    // Expose switchView globally for debugging and external access
    window.switchView = switchView;

    async function loadDashboard() {
        try {
            const response = await fetch('/dashboard_stats');
            const data = await response.json();

            // Update Greeting
            const greetingEl = document.getElementById('dashboard-greeting');
            const dateEl = document.getElementById('dashboard-date');
            if (greetingEl) {
                const hour = new Date().getHours();
                let greeting = 'Good morning';
                if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
                else if (hour >= 17) greeting = 'Good evening';
                greetingEl.textContent = `${greeting}, User!`;
            }
            if (dateEl) {
                const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
                dateEl.textContent = new Date().toLocaleDateString(undefined, options);
            }

            // Update Stats
            if (document.getElementById('stat-chats')) document.getElementById('stat-chats').textContent = data.total_chats;
            if (document.getElementById('stat-files')) document.getElementById('stat-files').textContent = data.total_files;
            if (document.getElementById('stat-events')) document.getElementById('stat-events').textContent = data.upcoming_events_count;

            // Update Knowledge Profile
            const knowledgeProfile = document.getElementById('knowledge-profile');
            if (knowledgeProfile) {
                knowledgeProfile.innerHTML = '';
                if (data.knowledge_profile && data.knowledge_profile.length > 0) {
                    data.knowledge_profile.forEach(item => {
                        const topic = item.topic;
                        const score = item.level;
                        const itemDiv = document.createElement('div');
                        itemDiv.classList.add('knowledge-item');
                        itemDiv.innerHTML = `
                            <div class="knowledge-header">
                                <span>${topic}</span>
                                <span>${Math.round(score)}%</span>
                            </div>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: ${score}%"></div>
                            </div>
                        `;
                        knowledgeProfile.appendChild(itemDiv);
                    });
                } else {
                    knowledgeProfile.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.9rem;">No quiz data yet. Take a quiz to see your stats!</p>';
                }
            }

            // Update Upcoming Events
            const dashboardEvents = document.getElementById('dashboard-events');
            if (dashboardEvents) {
                dashboardEvents.innerHTML = '';
                if (data.upcoming_events && data.upcoming_events.length > 0) {
                    data.upcoming_events.forEach(event => {
                        if (!event || !event.start) return;

                        const dateStr = event.start.dateTime || event.start.date;
                        if (!dateStr) return;

                        const startDate = new Date(dateStr);
                        const month = startDate.toLocaleDateString(undefined, { month: 'short' });
                        const day = startDate.getDate();
                        const time = startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                        const item = document.createElement('div');
                        item.classList.add('dashboard-list-item');
                        item.innerHTML = `
                            <div class="item-date-box">
                                <div class="date-month">${month}</div>
                                <div class="date-day">${day}</div>
                            </div>
                            <div class="item-content">
                                <h4>${event.summary || 'No Title'}</h4>
                                <p>${time}</p>
                            </div>
                        `;
                        dashboardEvents.appendChild(item);
                    });
                } else {
                    dashboardEvents.innerHTML = '<p style="color: var(--text-secondary); padding: 1rem;">No upcoming events.</p>';
                }
            }

        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    async function deleteSession(sessionId) {
        try {
            await fetch(`/delete_session/${sessionId}`, { method: 'DELETE' });
            if (sessionId === currentSessionId) {
                createNewChat();
            }
            loadSessions();
        } catch (error) {
            console.error('Error deleting session:', error);
        }
    }

    async function loadSession(sessionId) {
        if (sessionId === currentSessionId) return;

        try {
            const response = await fetch(`/history/${sessionId}`);
            const history = await response.json();

            currentSessionId = sessionId;
            if (chatMessages) {
                chatMessages.innerHTML = '';

                history.forEach(msg => {
                    const sender = msg.role === 'model' ? 'agent' : 'user';
                    addMessage(msg.content, sender);
                });
            }

            loadSessions();
        } catch (error) {
            console.error('Error loading session:', error);
        }
    }

    function switchView(view) {
        if (view === 'chat') {
            chatArea.classList.remove('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.add('active');
            navTasks.classList.remove('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.remove('active');
        } else if (view === 'tasks') {
            chatArea.classList.add('hidden');
            tasksArea.classList.remove('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.remove('active');
            navTasks.classList.add('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.remove('active');
            fetchEvents();
        } else if (view === 'dashboard') {
            chatArea.classList.add('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.remove('hidden');
            quizzesArea.classList.add('hidden');
            navChat.classList.remove('active');
            navTasks.classList.remove('active');
            navDashboard.classList.add('active');
            navQuizzes.classList.remove('active');
            loadDashboard();
        } else if (view === 'quizzes') {
            chatArea.classList.add('hidden');
            tasksArea.classList.add('hidden');
            dashboardArea.classList.add('hidden');
            quizzesArea.classList.remove('hidden');
            navChat.classList.remove('active');
            navTasks.classList.remove('active');
            navDashboard.classList.remove('active');
            navQuizzes.classList.add('active');
            quizSelection.classList.remove('hidden');
            quizContent.classList.add('hidden');
        }
    }

    // Expose switchView globally for debugging and external access
    window.switchView = switchView;

    async function loadDashboard() {
        try {
            const response = await fetch('/dashboard_stats');
            const data = await response.json();

            // Update Greeting
            const greetingEl = document.getElementById('dashboard-greeting');
            const dateEl = document.getElementById('dashboard-date');
            if (greetingEl) {
                const hour = new Date().getHours();
    
