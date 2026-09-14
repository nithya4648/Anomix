import React from 'react'
import { useNavigate } from 'react-router-dom'
import RuleConfigPanel from '../components/RuleConfigPanel'

export const AlertRules: React.FC = () => {
  const navigate = useNavigate()

  return <RuleConfigPanel onClose={() => navigate('/')} />
}

export default AlertRules
