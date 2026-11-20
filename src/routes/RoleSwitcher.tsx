import React from 'react';

interface RoleSwitcherProps {
  className?: string;
}

/**
 * RoleSwitcher is deactivated to enforce strict single-interface access.
 * Users must authenticate to access their assigned role interface.
 */
export const RoleSwitcher: React.FC<RoleSwitcherProps> = () => {
  return null;
};
