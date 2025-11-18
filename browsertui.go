package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"regexp"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	bgColor		= lipgloss.Color("#2B1B17")
	fgColor		= lipgloss.Color("#E3CBA8")
	headerCol	= lipgloss.Color("#A67B5B")
)

type model struct {
	url		string
	body	string
	error	string
	loaded	bool
}

func initialModel(url string) model {
	return model{url: url, loaded: false}
}

func fetchAndClean(url string) (string, error) {
	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	html := string(data)
	re := regexp.MustCompile("<[^>]*>")
	clean := re.ReplaceAllString(html, "")

	return clean, nil
}

func (m model) Init() tea.Cmd {
	return func() tea.Msg {
		body, err := fetchAndClean(m.url)
		if err != nil {
			return errMsg{err}
		}
		return bodyMsg(body)
	}
}

type bodyMsg string
type errMsg struct{ err error }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case bodyMsg:
		m.body = string(msg)
		m.loaded = true
		return m, nil

	case errMsg:
		m.error = msg.err.Error()
		m.loaded = true
		return m, nil
	}
	return m, nil
}

func (m model) View() string {
	header := lipgloss.NewStyle().Foreground(headerCol).Bold(true).Render("[ Mocha-Caffé TUI Browser ]\nURL: " + m.url + "\n")

	contentStyle := lipgloss.NewStyle().Foreground(fgColor).Background(bgColor).Padding(1, 2)

	if !m.loaded {
		return header + contentStyle.Render("Loading......")
	}

	if m.error != "" {
		return header + contentStyle.Render("Error: " + m.error)
	}

	return header + contentStyle.Render(m.body)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: browsertui <url>")
		return
	}

	url := os.Args[1]
	p := tea.NewProgram(initialModel(url))
	if err := p.Start(); err != nil {
		fmt.Println("Error running TUI:", err)
		os.Exit(1)
	}
}
