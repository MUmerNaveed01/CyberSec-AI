import { render, screen } from '@/test-utils';
import LoginPage from '@/app/(auth)/login/page';

// Mock the useRouter hook
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />);
    expect(screen.getByText('CyberShield AI')).toBeInTheDocument();
  });

  it('shows email and password fields', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('password field is type password', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
  });
});