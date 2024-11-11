import tkinter as tk
from tkinter import scrolledtext
import pyperclip


class LLMInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Requirements and Personas Interface")

        self._initialize_widgets()

        self.system_description = ""
        self.history = []
        self.stakeholders = {}
        self.requirements = {}
        self.personas = {}
        self.answers = {}

        self.questions = [
            "Describe the basic idea of the system.",
            "What is the purpose of your system?",
            "Who are the target users of your system?",
            "What external systems does the target system interact or integrate with?",
            "How does the user interact with the system?",
            "What technology is the system built with?",
            "Define the system boundaries.",
            "Are there any challenges or areas where the system should focus on?",
        ]
        self.current_question_idx = 0
        self.mode = "system_description"

        self.ask_next_question()

    def _initialize_widgets(self):
        """Setup interface widgets."""
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled', width=80, height=20, font=("Arial", 10)
        )
        self.chat_display.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        self.user_input = tk.Text(self.root, width=70, height=4, font=("Arial", 12), wrap=tk.WORD)
        self.user_input.grid(column=0, row=1, padx=10, pady=10, sticky='w')

        self.submit_button = tk.Button(self.root, text="Send", command=self.process_input)
        self.submit_button.grid(column=1, row=1, padx=10, pady=10, sticky='e')

    def _append_chat(self, text, sender="System"):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {text}\n\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def _copy_to_clipboard(self, text):
        pyperclip.copy(text)
        self._append_chat("--- Prompt copied to clipboard ---", sender="System")

    def ask_next_question(self):
        if self.current_question_idx < len(self.questions):
            self._append_chat(self.questions[self.current_question_idx], sender="System")
        else:
            self._finalize_system_description()

    def process_input(self):
        user_input = self.user_input.get("1.0", tk.END).strip()
        if not user_input:
            return

        self._append_chat(user_input, sender="User")
        self.history.append({"User": user_input})
        self.user_input.delete("1.0", tk.END)

        {
            "system_description": self._process_system_description,
            "waiting_for_llm_response": self._handle_llm_response,
            "stakeholders": self._process_stakeholders,
            "add_missing_stakeholders": self._add_missing_stakeholders,
            "requirements": self._process_requirements,
            "add_own_requirements": self._handle_add_own_requirements,
            "adding_requirements": self._add_user_requirements,
            "persona": self._process_personas
        }.get(self.mode, lambda: None)(user_input)

    def _process_system_description(self, user_input):
        self.answers[self.questions[self.current_question_idx]] = user_input
        self.current_question_idx += 1
        self.ask_next_question()

    def _finalize_system_description(self):
        prompt = "\n".join([f"{q}\n{a}" for q, a in self.answers.items()])
        system_prompt = (
            "You are a requirements engineer. Based on the provided details, write a comprehensive system description using the NABC framework (Need, Approach, Benefit, Competition). Clearly define the target audience's primary needs, the specific approach the system will take, the measura-ble benefits it will deliver, and a summary of any competing solutions. Ensure clarity and conciseness in the description.\n\n"
            f"{prompt}"
        )
        self._copy_to_clipboard(system_prompt)
        self._append_chat(
            "Paste this in the LLM input field and chat until it understands the system. Once ready, paste the LLM's response here to continue.")
        self.mode = "waiting_for_llm_response"

    def _handle_llm_response(self, user_input):
        self.system_description = user_input
        self.mode = "stakeholders"
        self._ask_stakeholder_prompt()

    def _ask_stakeholder_prompt(self):
        stakeholder_prompt = (
            "Based on the system description, list all potential stakeholders relevant to the system's success, using the format 'Name: Description'."
        )
        self._copy_to_clipboard(stakeholder_prompt)
        self._append_chat("Paste this in the LLM input field and return its response here to continue.")

    def _process_stakeholders(self, user_input):
        self.stakeholders = dict(line.split(":", 1) for line in user_input.splitlines() if ":" in line)
        self._append_chat("--- Stakeholders Identified ---", sender="System")
        self._append_chat("Would you like to add any additional stakeholders? (yes/no)", sender="System")
        self.mode = "add_missing_stakeholders"

    def _add_missing_stakeholders(self, user_input):
        if user_input.lower() == "yes":
            self._append_chat("Please add stakeholders in the format 'Name: Description'", sender="System")
        else:
            self.mode = "requirements"
            self._ask_requirements_prompt()

    def _ask_requirements_prompt(self):
        self.stakeholder_list = list(self.stakeholders.keys())
        self.current_stakeholder_idx = 0
        self._request_requirements()

    def _request_requirements(self):
        if self.current_stakeholder_idx < len(self.stakeholder_list):
            current_stakeholder = self.stakeholder_list[self.current_stakeholder_idx]
            prompt = (
                f"For '{current_stakeholder}: {self.stakeholders[current_stakeholder]}', list requirements specific to this stakeholder’s needs or interactions with the system. Use the format 'Requirement Name: Description.' Focus on clear, actionable needs that directly support this stakeholder’s role or goals. Write the requirements testable."
            )
            self._copy_to_clipboard(prompt)
            self._append_chat(f"--- Requirement prompt for '{current_stakeholder}' copied ---", sender="System")
        else:
            self._display_final_results()

    def _process_requirements(self, user_input):
        current_stakeholder = self.stakeholder_list[self.current_stakeholder_idx]
        self.requirements[current_stakeholder] = [line for line in user_input.splitlines() if ":" in line]
        self._append_chat(f"--- Requirements for '{current_stakeholder}' Identified ---", sender="System")
        self._append_chat("Would you like to add additional requirements? (yes/no)", sender="System")
        self.mode = "add_own_requirements"

    def _handle_add_own_requirements(self, user_input):
        if user_input.lower() == "yes":
            self._append_chat("List additional requirements in 'Requirement Name: Description' format.",
                              sender="System")
            self.mode = "adding_requirements"
        else:
            self.mode = "persona"
            self._request_persona()

    def _add_user_requirements(self, user_input):
        current_stakeholder = self.stakeholder_list[self.current_stakeholder_idx]
        self.requirements[current_stakeholder].extend([line for line in user_input.splitlines() if ":" in line])
        self._append_chat("--- Additional requirements added ---", sender="System")
        self.mode = "persona"
        self._request_persona()

    def _request_persona(self):
        current_stakeholder = self.stakeholder_list[self.current_stakeholder_idx]
        persona_prompt = (
                f"Create a detailed, role-specific persona for '{current_stakeholder}' based on the requirements listed:\n"+
                "\n".join(self.requirements[current_stakeholder])+
                "Avoid to write re-quirements for the system inside the persona. Focus instead on the stakeholder’s background, primary motivations, goals, and pain points."
        )
        self._copy_to_clipboard(persona_prompt)
        self._append_chat(f"--- Persona prompt for '{current_stakeholder}' copied ---", sender="System")

    def _process_personas(self, user_input):
        current_stakeholder = self.stakeholder_list[self.current_stakeholder_idx]
        self.personas[current_stakeholder] = user_input
        self.current_stakeholder_idx += 1

        if self.current_stakeholder_idx < len(self.stakeholder_list):
            self.mode = "requirements"
            self._request_requirements()
        else:
            self._display_final_results_in_new_window()

    def _display_final_results_in_new_window(self):
        result_text = "\n\n".join([
            f"Stakeholder: {stakeholder}\nDescription: {self.stakeholders[stakeholder]}\n\n"
            f"Requirements:\n" + "\n".join(self.requirements[stakeholder]) + "\n\n"
                                                                             f"Persona:\n{self.personas[stakeholder]}"
            for stakeholder in self.stakeholder_list
        ])

        results_window = tk.Toplevel(self.root)
        results_window.title("Final Results")

        results_display = scrolledtext.ScrolledText(
            results_window, wrap=tk.WORD, width=80, height=20, font=("Arial", 10)
        )
        results_display.insert(tk.END, result_text)
        results_display.configure(state='disabled')
        results_display.pack(padx=10, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = LLMInterface(root)
    root.mainloop()
