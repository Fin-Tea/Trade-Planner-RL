from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from enum import Enum
import copy

class TradeActions(Enum):
    EXECUTE_TRADE = 1,
    EXECUTE_TRADE_WITH_CAUTION = 2,
    DONT_EXECUTE_TRADE = 3

DEFAULT_STATE = {
        'is_good_mood': 0,
        'is_good_energy': 0,
        'is_bad_mood': 0,
        'is_low_energy': 0,
        'has_trade_plan': 0,
        'is_revenge_trade': 0,
        'is_good_trade_setup': 0,
        'has_trade_confirmations': 0,
        'is_good_trade_confirmations': 0,
        'has_good_rr_ratio': 0,
        'has_executed_trade': 0,
        'is_would_have_been_profitable': 0,
        'is_profitable_trade': 0,
        'has_followed_plan_completely': 0,
        'has_followed_plan_partially': 0,
        'has_not_followed_plan_at_all': 0,
        'has_exited_early': 0,
        'has_stopped_out_late': 0, 
        'is_good_time_of_day_to_trade': 0,
        'is_high_daily_s_and_p_volume': 0,
        'is_high_daily_vix_volatility': 0,
        'is_good_instrument_conditions': 0,
        'is_high_daily_instrument_volume': 0,
        'is_high_daily_instrument_atr': 0,
        'is_high_current_instrument_volume': 0,
        'is_high_current_instrument_atr': 0,
        'is_high_current_instrument_rsi': 0,
        'is_low_current_instrument_rsi': 0,
        'is_bullish_trend_day':0,
        'is_range_trading_day': 0,
        'is_bearish_trend_day':0,
        'is_good_financial_instrument_to_trade': 0,
        'is_okay_financial_instrument_to_trade': 0,
        'is_bad_financial_instrument_to_trade': 0,
        'is_good_position_size': 0,
        'is_position_size_too_large': 0,
        'is_position_size_too_small': 0,
    }


class FinstrumentEnv(py_environment.PyEnvironment):

  def __init__(self):
    self._action_spec = array_spec.BoundedArraySpec(
        shape=(), dtype=np.int32, minimum=1, maximum=3, name='action')
    self._observation_spec = array_spec.BoundedArraySpec(
        shape=(1,37), dtype=np.int32, minimum=0, name='observation')
    self._state = copy.deepcopy(DEFAULT_STATE)
      
    self._episode_ended = False

  def action_spec(self):
    return self._action_spec

  def observation_spec(self):
    return self._observation_spec

  def _reset(self):
    self._state = copy.deepcopy(DEFAULT_STATE)
    self._episode_ended = False
    return ts.restart(np.array([self._state], dtype=np.int32)) # TODO: handle state conversion to array

  def _step(self, action):

    if self._episode_ended:
      # The last action ended the episode. Ignore the current action and start
      # a new episode.
      return self.reset()

    # Make sure episodes don't go on forever.
    # This is a re-learning model. Essentially the state doesn't know the result
      # The state knows a number of factors in advance of the trade result
      # and makes a decision about whether or not it should trade, with the goal being profitability
      # so it will pick an action not knowing the trade result and then compare 
      # the action to the trade result (whether or not the trade should have been executed based on profitability)
      # (while this is an oversimplification, more nuances can be added later. right now,
      # just focus on when to execute trades and when not to. In the future, there can be suggestions
      # such as, scale down (or scale up), enter earlier, increase/decrease risk amount, etc. start small!)
      # 

    has_executed_trade = False
    is_would_have_been_profitable = False

    if action == TradeActions.EXECUTE_TRADE or action == TradeActions.EXECUTE_TRADE_WITH_CAUTION:
        has_executed_trade = True
    elif action == TradeActions.DONT_EXECUTE_TRADE:
        # update is_would_have_been_profitable based on input trade result
    else:
      raise ValueError('`action` should be from TradeActions.')

    # the action should be picked based on the pre-trade execution state
    # then the action must be compared to the trade result
    # then the trade plan reward will be calculated
    # start simple! in this version there are no step transitions.
    # each step has a termination. and each trade is an episode.
    # the goal of the DQN is to map trade plans to 
    # probability of success. that's it. in the future, EXECUTE_TRADE_WITH_CAUTION
    # can have suggestions such as scaling down, adjusting risk, adjusting RR, adjusting exits, etc.

    reward = 250 

    return ts.termination(np.array(self._state.values(), dtype=np.int32), reward)
