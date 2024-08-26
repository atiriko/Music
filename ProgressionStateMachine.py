class ProgressionStateMachine:
    def __init__(self):
        self.state = None

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def perform_action(self):
        self.state.perform_action(self)

    def transition_to_next_state(self):
        self.state.transition_to_next_state(self)